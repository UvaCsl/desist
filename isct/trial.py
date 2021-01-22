import pathlib
import os

from .patient import Patient, patient_config
from .container import create_container
from .config import Config
from .runner import LocalRunner

trial_config = 'trial.yml'


class Trial(Config):
    """Representation of a trial."""
    # FIXME:
    # - provide often used properties through @property?
    # - provide function to obtain all patients, i.e. iterator?
    # - split `self.path` and `self.dir`?

    def __init__(self, path, sample_size=1, random_seed=1, config={},
                 runner=LocalRunner()):
        """Initialise a trial from given path."""

        path = pathlib.Path(path).joinpath(trial_config)

        # merge configuration
        config = {
            **{
                'sample_size': sample_size,
                'random_seed': random_seed
            },
            **config
        }
        super().__init__(path, config)

        # set often used properties
        # FIXME: remove these settings, or change to `@property`; shorten
        self.prefix = self.get('prefix', 'patient')
        self.sample_size = self.get('sample_size', sample_size)
        self.random_seed = self.get('random_seed', random_seed)
        self.runner = runner

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
        for i in range(0, self.sample_size):
            self.append_patient(i)

        self.sample_virtual_patient(0, self.sample_size)

    def append_patient(self, idx):
        """Append a virtual patient to trial."""
        patient = Patient(self.path.parent, idx, prefix=self.prefix)
        patient.create()

    def sample_virtual_patient(self, lower, upper):
        """Evaluate the virtual patient model."""

        local_path = pathlib.Path('/trial')
        patients = [local_path.joinpath(p) for p in self.patients]

        # FIXME: generalise this model
        model = 'virtual-patient-generation'

        container = create_container(model, runner=self.runner)
        container.bind(self.path.parent, local_path)
        container.run(args=' '.join(map(str, patients)))

    def run(self):
        """Run the full trial simulation."""

        patient_paths = map(lambda p: self.dir.joinpath(p), self.patients)
        for i, path in enumerate(patient_paths):
            patient = Patient.read(path.joinpath(patient_config), self.runner)
            patient.run()
