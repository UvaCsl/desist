import pathlib

from .config import Config
from .container import create_container
from .runner import Logger
from .events import Events, default_events, default_labels

patient_config = 'patient.yml'
patient_path = pathlib.Path('/patient')


class Patient(Config):
    def __init__(self,
                 path,
                 idx=0,
                 prefix='patient',
                 config={},
                 runner=Logger(),
                 ):
        """Initialise a Patient: path either basename or to patient.yml"""

        # form patient path from prefix and ID
        path = pathlib.Path(path)
        path = path.joinpath(f'{prefix}_{idx:05}')
        path = path.joinpath(patient_config)

        # assign command runner
        self.runner = runner

        # merges properties into config
        defaults = {
            'prefix': prefix,
            'id': idx,
            'events': default_events.to_dict(),
            'pipeline_length': len(list(default_events.models)),
            'labels': default_labels,
            'completed': False,
        }
        config = {**defaults, **config}
        super().__init__(path, config)

    @property
    def completed(self):
        """Indicates if all simulations are completed."""
        return self.get('completed', False)

    @completed.setter
    def completed(self, value: bool):
        """Setter routine for :meth:`~isct.patient.Patient.completed`."""
        self['completed'] = value

    @classmethod
    def read(cls, path, runner=Logger()):
        """Reads an existing patient configuration."""

        # obtain config from provided filepath
        config = super().read(path)

        # extract keyword arguments and reconstruct patient
        path = path.parent.parent
        idx, prefix = config['id'], config['prefix']

        return cls(path,
                   idx=idx,
                   prefix=prefix,
                   config=dict(config),
                   runner=runner)

    def create(self):
        """Create a patient directory with configuration files."""
        self.write()

    def run(self):
        """Evaluate simulation of virtual patient."""

        events = Events(self.get('events'))
        container_path = self.get('container-path')

        for idx, model in enumerate(events.models):
            container = create_container(f'{model}',
                                         container_path=container_path,
                                         runner=self.runner)
            container.bind(self.path.parent, patient_path)
            container.run(args=f'event --patient /patient --event {idx}')

        # FIXME: assert that all simulations worked as intended

        # Update the local configuration file only when the runner is able
        # to actually invoke the simulations, i.e. do not update the config
        # files when running with a verbose runner, e.g. a `Logger`.
        if self.runner.write_config:

            # FIXME: the marking of a patient simulation as `completed` could
            # be make more general by storing a completed boolean per event.
            # So, we can then set here
            # `self.completed = all([e.completed for e in events.models])
            self.completed = True
            self.write()
