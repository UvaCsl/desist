"""Trial configuration class.

This module contains two classes to represent an *in silico* trial of virtual
patients: :class:`Trial` and :class:`ParallelTrial`. Fundamentally, these
classes are a ``dict`` containing the configuration data for a *in silico*
trial. The trials are layed out as a single trial directory with subdirectories
for each virtual patient (see :class:`~isct.patient.Patient`). The trial's
configuration is stored at :attr:`isct.trial.trial_config` in YAML format.

:class:`Trial` provides routines to create :meth:`Trial.create` and run
:meth:`Trial.run` trials. For parallel evaluation of the patient simulation
pipelines :class:`ParallelTrial` provides functionality pipe the required
commands over ``stdout`` for evalation using `GNU Parallel`_.

.. _GNU Parallel:
    https://www.gnu.org/software/parallel/
"""

import pathlib
import os

from .patient import Patient, LowStoragePatient, patient_config
from .container import create_container
from .config import Config
from .runner import LocalRunner, Logger

trial_config = 'trial.yml'
"""str: Trial configuration filename and suffix."""

trial_path = pathlib.Path('/trial')
"""pathlib.Path: Trial directory inside the containerised environment.

In containerised environments the trial's directory will be bound to a local
path, here ``/trial`` that maps towards the trial directory on the host
machine. For details, see :meth:`isct.container.Container.bind`.
"""

# FIXME: generalise these model
virtual_patient_model = 'virtual-patient-generation'
trial_outcome_model = 'in-silico-trial-outcome'


class Trial(Config):
    """Representation of an *in silico* trial."""
    def __init__(
            self,
            path,
            sample_size=1,
            random_seed=1,
            config={},
            runner=LocalRunner(),
            keep_files=True,
    ):
        """Initialise a trial from given path and options.

        Args:
            path (str): Path to YAML file.
            sample_size (int): Number of patients to consider in the trial.
            random_seed (int): The random seed to use in the trial.
            config (dict): Dictionary with default configurations values.
            runner (:class:`~isct.runner.Runner`, optional): Command runner.
            keep_files (bool): If large files should be kept or deleted.
        """
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

        # store the behaviour to keep/clean files after patient simulations
        self.keep_files = keep_files

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
            patient['container-path'] = self.container_path

            if not self.keep_files:
                patient = LowStoragePatient.from_patient(patient)

            yield patient

    def __len__(self):
        """Returns the number of virtual patients considered in the trial.

        Counts the number of patients by exhausting the
        :meth:`~isct.trial.Trial.patients` generator.
        """
        return len(list(self.patients))

    @classmethod
    def read(cls, path, runner=Logger(), keep_files=True):
        """Initialises :class:`Trial` from the provided YAML file.

        First the basic :class:`~isct.config.Config` is initialised, afterwhich
        a :class:`Trial` instance is created from the discovered parameters.
        """
        config = super().read(path)
        return cls(path.parent,
                   sample_size=config.get('sample_size', 0),
                   random_seed=config.get('random_seed', 0),
                   config=dict(config),
                   runner=runner,
                   keep_files=keep_files)

    @property
    def container_path(self):
        """Returns ``container-path`` if present in :class:`Trial`.

        The ``container-path`` stores the directory containing the Singularity
        containers, see :class:`~isct.singularity.Singularity`.

        The container path is not resolved to an complete absolute path to
        allow passing a symbolic link as the container path that points to
        different locations on various systems:

            >>> "$HOME"/containers/ -> /local/user/path/to/containers
            >>>                     -> /mount/user/path/to/containers
        """
        # FIXME: assert behaviour with symbolic links through additional tests

        if path := self.get('container-path', None):
            return path
        return None

    def invalid_container_path(self):
        """Returns true when no or invalide container paths are encountered."""
        return self.container_path and not os.path.exists(self.container_path)

    @property
    def patients(self):
        """Iterator yielding all patient paths of the trial."""
        for patient in os.listdir(self.dir):
            if os.path.isdir(self.dir.joinpath(patient)):
                yield patient

    def create(self):
        """Create a trial and the virtual patients.

        Creates a trial directory including the trial's configuration file
        :attr:`isct.trial.trial_config` in YAML format. For each patient
        a patient directory is initialised with a patient configuration
        present.

        The patient configuration are filled with statistical samples from the
        ``virtual patient model`` by invoking
        :meth:`Trial.sample_virtual_patient`.
        """
        # write configuration to disk
        self.write()

        # create patients
        for i in range(self.get('sample_size', 0)):
            patient = Patient(self.path.parent,
                              idx=i,
                              prefix=self.get('prefix'))
            patient.create()

        self.sample_virtual_patient(0, self.get('sample_size'))

    def append_patient(self, idx: int):
        """Extend the trial with a single virtual patient.

        The sample size is incremented when calling this function.

        Args:
            idx (int): integer value of the to be appended patient.
        """
        patient = Patient(self.path.parent, idx=idx, prefix=self.get('prefix'))
        patient.create()

        # increment the sample size when appending patients
        self['sample_size'] += 1
        self.write()

    def sample_virtual_patient(self, lower: int, upper: int):
        """Update patients' configurations using the virtual patient model.

        For each virtual patient with their index between ``lower`` and
        ``upper`` the ``virtual patient model`` is evaluated. This model
        provides statistical samples for the virtual
        :class:`~isct.patient.Patient`. If the configuration files already
        exist, the statistical samples are overwritten.

        The ``upper`` bound is exclusive similar to ``range``

        >>> trial.sample_virtual_patient(4, 8)
        [patient_00004, ..., patient_00007]

        Args:
            lower (int): lower bound of the range of patients to sample.
            upper (int): upper bound of the range of patients to sample.
        """
        err = f'Samples the empty set: received ID range [{lower}:{upper}]'
        assert lower < upper, err

        # truncate the patients from lower to upper
        patients = sorted([trial_path.joinpath(p) for p in self.patients])
        patients = patients[lower:upper]

        container = create_container(virtual_patient_model,
                                     container_path=self.container_path,
                                     runner=self.runner)
        container.bind(self.path.parent, trial_path)

        # The trial.yml config file is passes as the criteria file for the
        # virtual patient model.
        args = ' '.join(map(str, patients))
        args = f"{args} --config {str(trial_path.joinpath(trial_config))}"

        container.run(args=args)

    def outcome(self):
        """Evaluate the trial outcome model."""
        container = create_container(trial_outcome_model,
                                     container_path=self.container_path,
                                     runner=self.runner)
        container.bind(self.path.parent, trial_path)
        container.run()

    def run(self, skip_completed=False):
        """Runs the full trial simulation.

        Evaluates the simulation of all virtual patients present in the
        current trial. The patients are evaluated in sorted order, where the
        patients are sorted based on the patient directories.

        Args:
            skip_completed (bool): Skip already completed patients
        """
        # exhaust all patients present in the iterator
        for patient in self:
            if skip_completed and patient.completed:
                continue

            patient.run()


class ParallelTrial(Trial):
    """Parallel evaluation of patient simulations using `GNU Parallel`_."""
    def run(self, skip_completed=False):
        """Pipe the simulation commands over ``stdout``.

        Rather than directly evaluating the patient simulations, as done
        in :meth:`Trial.run`, the patient run
        (:meth:`~isct.patient.Patient.run`) commands are piped over ``stdout``.
        This stream of commands is intended to be piped into `GNU Parallel`_,
        which then takes control over the parallel evaluation of the patient
        simulations.

        Args:
            skip_completed (bool): Skip already completed patients.

        Examples:
            >>> isct -v trial run --parallel | parallel -j 4
        """
        # additional flags to pass into the emitted instructions
        flags = '--keep-files' if self.keep_files else '--clean-files'

        for p in self:
            if skip_completed and p.completed:
                continue
            cmd = f'isct --log {p.dir}/isct.log patient run {flags} {p.dir}'
            self.runner.run(cmd.split())
