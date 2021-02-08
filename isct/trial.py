import pathlib
import os

from .patient import Patient, patient_config
from .container import create_container
from .config import Config
from .runner import LocalRunner, Logger

trial_config = 'trial.yml'
trial_path = pathlib.Path('/trial')


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

        # FIXME: generalise this model
        model = 'virtual-patient-generation'

        container = create_container(model,
                                     container_path=self.container_path,
                                     runner=self.runner)
        container.bind(self.path.parent, trial_path)
        container.run(args=' '.join(map(str, patients)))

    def run(self):
        """Run the full trial simulation."""

        patient_paths = map(lambda p: self.dir.joinpath(p), self.patients)
        for i, path in enumerate(sorted(list(patient_paths))):
            config = path.joinpath(patient_config)
            patient = Patient.read(config, runner=self.runner)
            patient.run(container_path=self.container_path)


class ParallelTrial(Trial):
    # For parallel execution _enumerate_ the required patient
    # commands that need to be considered for the current trial.
    def run(self):
        patient_paths = map(lambda p: self.dir.joinpath(p), self.patients)
        for i, path in enumerate(sorted(list(patient_paths))):
            config = path.joinpath(patient_config)
            patient = Patient.read(config, runner=self.runner)

            cmd = f'isct --log {path}/isct.log patient run {patient.path}'
            self.runner.run(cmd.split())
