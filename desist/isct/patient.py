"""A patient configuration.

Extends the configuration functionality :class:`~isct.config.Config` with
additional patient specific functionality.
"""
import pathlib

from .config import Config
from .container import create_container
from .runner import Logger
from .events import Events, default_events, default_labels
from .utilities import clean_large_files

patient_config = 'patient.yml'
patient_path = pathlib.Path('/patient')


class Patient(Config):
    """A virtual patient represented by its configuration file."""
    def __init__(
            self,
            path,
            idx=0,
            prefix='patient',
            config={},
            runner=Logger(),
    ):
        """Initialise a virtual patient.

        Args:
            path: The directory where the patient is stored on the file system.
            idx: The index of the current patient, i.e. the patient's ID.
            prefix: The directory prefix.
            config: A default patient configuration to extend.
            runner: The desired command evaluation.
        """
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

        path = pathlib.Path(path)

        # obtain config from provided filepath
        config = super().read(path)

        # extract keyword arguments and reconstruct patient
        idx, prefix = config['id'], config['prefix']

        # initialise a configuration class from the extracted parameters
        patient = cls(path.parent.parent,
                      idx=idx,
                      prefix=prefix,
                      config=dict(config),
                      runner=runner)

        # Note: the path set by initialising the class assumes the default
        # formatting conventions using the provided `prefix` and a set of
        # leading zeros. In cases were patient directories were generated with
        # other conventions, these paths will _not_ match. Thus, as a fallback
        # the configuration's path is set to what the user provided, assuming
        # this is the correct path.
        if patient.path != path:
            patient.path = path

        return patient

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
            container.bind(self.dir, patient_path)
            args = f'event --patient /patient --event {idx}'
            success = container.run(args=args)

            # Here we assert with `not False` to allow `None` as valid output
            # too. Any verbose logger, i.e. the command is simply logged or
            # printed to the console, does not have a notion of success/failure
            # and will sipmly return None. Thus, only when the runner can
            # make a meaningful conclusion on success/failure will True/False
            # values be returned.
            assert success is not False, "Patient event simulation failed."

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

    def reset(self):
        """Resets the status of a patient.

        This unsets the completed flag to ``False``, such that the patient
        is not marked as completed anymore and will be evaluated again in
        subsequent pipeline evaluations.
        """
        self.completed = False
        self.write()


class LowStoragePatient(Patient):
    """A low storage variant of the patient.

    After the simulation pipeline is completed, all files larger than
    `isct.utilities.MAX_FILE_SIZE` are deleted. This ensures litte data is
    aggregated along large cohorts of virtual patients.
    """

    @classmethod
    def from_patient(cls, patient):
        """Initialise a LowStoragePatient from a patient class."""
        return cls.read(patient.path, runner=patient.runner)

    def run(self):
        """Cleans simulation output after all models are completed."""
        super().run()
        clean_large_files(self.dir)
