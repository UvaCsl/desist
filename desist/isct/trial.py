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
from .utilities import CleanFiles, is_bind_path

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
            clean_files=CleanFiles.NONE,
    ):
        """Initialise a trial from given path and options.

        Args:
            path (str): Path to YAML file.
            sample_size (int): Number of patients to consider in the trial.
            random_seed (int): The random seed to use in the trial.
            config (dict): Dictionary with default configurations values.
            runner (:class:`~isct.runner.Runner`, optional): Command runner.
            clean_files (CleanFiles): If large files should be kept or deleted.
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
        self.clean_files = clean_files

    def __iter__(self):
        """Iterable over the patients in the trial.

        The iterator of `Trial` yields a patient instance for each patient
        present in the trial. The patients are yielded in sorted order, where
        the sort is based on their directory.
        """
        for path in sorted(list(self.patients)):
            config_path = path.joinpath(patient_config)
            patient = Patient.read(config_path, runner=self.runner)

            # Insert the `container-path` directory from the trial config file
            # into the patient configuration to propagate the container
            # directory into the patient instance.
            patient['container-path'] = self.container_path

            if self.clean_files == CleanFiles.NONE:
                yield patient
            else:
                yield LowStoragePatient.from_patient(patient, self.clean_files)

    def __len__(self):
        """Returns the number of virtual patients considered in the trial.

        Counts the number of patients by exhausting the
        :meth:`~isct.trial.Trial.patients` generator.
        """
        return len(list(self.patients))

    @classmethod
    def read(cls, path, runner=Logger(), clean_files=CleanFiles.NONE):
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
                   clean_files=clean_files)

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

    @container_path.setter
    def container_path(self, path):
        self['container-path'] = str(path)

    def invalid_container_path(self):
        """Returns true when no or invalide container paths are encountered."""
        return self.container_path and not os.path.exists(self.container_path)

    @property
    def patients(self):
        """Iterator yielding all valid patient paths of the trial.

        The iterator only considers entries in ``self.dir`` that can
        successfully be parsed as a ``Patient`` class to be part of the patient
        list considered in this trial.
        """
        def valid_patient(path):
            """Return ``true`` when reading a ``Patient`` successfully."""
            path = path.joinpath(patient_config)
            try:
                Patient.read(path)
                return True
            except (FileNotFoundError):
                return False

        patient_paths = (self.dir.joinpath(p) for p in os.listdir(self.dir))
        patient_paths = filter(os.path.isdir, patient_paths)
        patient_paths = filter(valid_patient, patient_paths)
        for patient_path in patient_paths:
            yield patient_path

    def patient_related_configuration(self):
        """Returns a dictionary of patient relevant configuration settings.

        This extracts settings of interest for the patient configuration that
        is specified globally for the trial, e.g. this extracts global pipeline
        specifications.
        """
        required_keys_for_patient = ['events', 'labels']
        return {k: self[k] for k in required_keys_for_patient if k in self}

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
            patient = Patient(self.dir,
                              idx=i,
                              prefix=self.get('prefix'),
                              config=self.patient_related_configuration())
            patient.create()

        self.sample_virtual_patient(0, self.get('sample_size'))
        return self

    def append_patient(self, idx: int):
        """Extend the trial with a single virtual patient.

        The sample size is incremented when calling this function.

        Args:
            idx (int): integer value of the to be appended patient.
        """
        patient = Patient(self.dir,
                          idx=idx,
                          prefix=self.get('prefix'),
                          config=self.patient_related_configuration())
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
        patients = sorted([trial_path.joinpath(p.name) for p in self.patients])
        patients = patients[lower:upper]

        container = create_container(virtual_patient_model,
                                     container_path=self.container_path,
                                     runner=self.runner)
        container.bind(self.dir, trial_path)

        # The trial.yml config file is passes as the criteria file for the
        # virtual patient model.
        args = ' '.join(map(str, patients))
        args = f"{args} --config {str(trial_path.joinpath(trial_config))}"

        container.run(args=args)

    def outcome(self, reference_trial=None):
        """Evaluate trial outcome model and perform optional trial comparison.

        Args:
            reference_trial: a path pointing to the reference trial.
        """
        container = create_container(trial_outcome_model,
                                     container_path=self.container_path,
                                     runner=self.runner)
        container.bind(self.dir, trial_path)

        if reference_trial is None:
            return container.run()

        reference_trial = str(pathlib.Path(reference_trial).resolve())

        if is_bind_path(reference_trial):
            host, local = reference_trial.split(':', maxsplit=1)
        else:
            host = reference_trial
            local = "/comp_trial"

        # The reference path is bound and the container responsible for
        # performing the trial outcome is notified of its presence by passing
        # along `--compare`.
        container.bind(host=host, local=local)
        args = f'--compare {local}'
        container.run(args=args)

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
        # By default files are to be cleaned: running in parallel can quickly
        # accumulate large amounts of data.
        file_flags = ['--clean-files', self.clean_files.value]

        # Only pass a container flag when the container path is set, i.e.
        # when running with Singularity-based containers. Note: this does
        # pick up externally set container paths, to allow to redirect to
        # another container path with respect to the original container path.
        container_flag = []
        if self.container_path:
            container_flag = ['--container-path', f'{self.container_path}']

        for patient in self:
            if skip_completed and patient.completed:
                continue

            # This only emits the directory of the patient path, this makes
            # it easier to generate a task list of patient simulation to
            # be performed from different directories.
            patient_path = os.path.dirname(patient.path)

            # build the command: the root command with a logger, followed
            # by the patient subcommand with additional flags.
            cmd = ['desist']
            cmd += ['--log', f'{patient_path}/isct.log']
            cmd += ['patient', 'run']
            cmd += file_flags + container_flag
            # The patient path is added last, such that it becomes easier to
            # slice out the patient directory of the list of parallel
            # simulations, i.e. the directories of interest are simply the
            # last item in the command.
            cmd += [f'{patient_path}']

            self.runner.run(cmd)


class QCGTrial(ParallelTrial):
    """Parallel evaluation of patient simulation using ``QCG-PilotJob``."""
    def run(self, skip_completed=False):
        """Run all patient simulations using ``QCG-PilotJob``.

        Rather than directly evaluating the patient simulations, as done in
        :meth:`Trial.run`, or piping the jobs over ``stdout`` as in
        :meth:`Parallel.run`, this ``run`` command inserts the required jobs
        into the ``QCG-PilotJob`` manager. After all jobs are submitted, the
        responsibility for scheduling and evaluating the required job queue is
        handed over to ``QCG`` through the :class:`~isct.runner.QCGRunner`.

        This routine waits until all jobs are evaluated on the available
        resources and ``QCG`` terminates.
        """
        super().run(skip_completed=skip_completed)
        self.runner.wait()
