import pathlib
import os

from .patient import Patient, patient_config
from .container import create_container
from .config import Config
from .runner import LocalRunner, Logger

trial_config = 'trial.yml'
trial_path = pathlib.Path('/trial')

# FIXME: generalise this model
virtual_patient_model = 'virtual-patient-generation'


class Trial(Config):
    """Representation of a trial."""
    def __init__(self,
                 path,
                 sample_size=1,
                 random_seed=1,
                 config={},
                 runner=LocalRunner()):
        """Initialise a trial from given path."""

        # path to patient configuration file `path/trial.yml`
        path = pathlib.Path(path).joinpath(trial_config)

        # overwrite defaults with read `config`
        defaults = {
            'container-path': None,
            'prefix': 'patient',
            'random_seed': random_seed,
            'sample_size': sample_size,
        }
        defaults.update(config)

        # parse default configuration
        super().__init__(path, defaults)

        # store the runner and container type
        self.runner = runner

    def __iter__(self):
        """Iterable over the patients in the trial.

        The iterator of `Trial` yields a patient instance for each patient
        present in the trial. The patients are yielded in sorted order, where
        the sort is based on their directory.
        """

        patient_paths = map(lambda p: self.dir.joinpath(p), self.patients)
        for path in sorted(list(patient_paths)):
            config_path = path.joinpath(patient_config)
            patient = Patient.read(config_path, runner=self.runner)

            # Insert the `container-path` directory from the trial config file
            # into the patient configuration to propagate the container
            # directory into the patient instance.
            patient |= {'container-path': self.container_path}

            yield patient

    def __len__(self):
        """Returns the number of virtual patients considered in the trial.

        Counts the number of patients by exhausting the
        :meth:`~isct.trial.Trial.patients` generator.
        """
        return len(list(self.patients))

    @classmethod
    def read(cls, path, runner=Logger()):
        config = super().read(path)
        return cls(path.parent,
                   sample_size=config['sample_size'],
                   random_seed=config['random_seed'],
                   config=dict(config),
                   runner=runner)

    @property
    def container_path(self):
        path = self.get('container-path', None)
        if path:
            return pathlib.Path(path)
        return None

    def invalid_container_path(self):
        """Returns true when no or invalide container paths are encountered."""
        return self.container_path and not self.container_path.exists()

    @property
    def patients(self):
        for patient in os.listdir(self.dir):
            if os.path.isdir(self.dir.joinpath(patient)):
                yield patient

    def create(self):
        """Create a trial and patients."""

        # write configuration to disk
        self.write()

        # create patients
        for i in range(0, self.get('sample_size')):
            self.append_patient(i)

        self.sample_virtual_patient(0, self.get('sample_size'))

    def append_patient(self, idx):
        """Append a virtual patient to trial."""
        patient = Patient(self.path.parent, idx=idx, prefix=self.get('prefix'))
        patient.create()

    def sample_virtual_patient(self, lower, upper):
        """Evaluate the virtual patient model."""

        patients = [trial_path.joinpath(p) for p in self.patients]

        container = create_container(virtual_patient_model,
                                     container_path=self.container_path,
                                     runner=self.runner)
        container.bind(self.path.parent, trial_path)
        container.run(args=' '.join(map(str, patients)))

    def run(self):
        """Invokes the simulation pipeline for each patient in the trial."""

        # exhaust all patients present in the iterator
        for patient in self:
            patient.run()


class ParallelTrial(Trial):
    # For parallel execution _enumerate_ the required patient
    # commands that need to be considered for the current trial.
    def run(self):
        for p in self:
            cmd = f'isct --log {p.dir}/isct.log patient run {p.path}'
            self.runner.run(cmd.split())
