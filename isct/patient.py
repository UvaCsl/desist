import pathlib

from .config import Config
from .container import create_container
from .runner import Logger
from .events import Events, default_events

patient_config = 'patient.yml'
patient_path = pathlib.Path('/patient')


class Patient(Config):
    def __init__(self,
                 path,
                 idx=0,
                 prefix='patient',
                 config={},
                 runner=Logger()):
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
            # FIXME: the labels _have_ to be generated/generic?
            'labels': {
                'place-clot': 'place-clot'
            }
        }
        config = {**defaults, **config}
        super().__init__(path, config)

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

    def run(self, container_path=None):
        """Evaluate simulation of virtual patient."""

        events = Events(self.get('events'))

        for idx, model in enumerate(events.models):
            container = create_container(f'{model}',
                                         container_path=container_path,
                                         runner=self.runner)
            container.bind(self.path.parent, patient_path)
            container.run(args=f'event --patient /patient --event {idx}')
