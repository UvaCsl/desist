import click
import collections
import logging
import os
import pathlib
import shutil

from .config import Config
from .trial import Trial, ParallelTrial, trial_config
from .runner import new_runner


@click.group()
def trial():
    """Trial

    The `trial` command provides interaction with in silico computational
    trials. This command allows to create cohorts of virtual patients, run
    all simulation pipelines for the considered cohort, and analyse the
    outcome of a specific trial.
    """


def assert_container_path(trial):
    """Raises `UsageError` for invalid Singularity container paths.

    The trial configuration `/path/trial.yml` can contain a key relating to the
    filesystem path where the Singularity containers are stored. If this key
    is missing or if the key equals `null` in YAML (i.e. None in Python), it
    is assumed Docker container formats are used.

    However, if the `container-path` key is present in the trial configuration,
    the path points towards the directory where the considered Singularity
    containers were stored. If this path is missing, we need to raise a
    `UsageError` as the simulations cannot be executed, i.e. the Singularity
    containers cannot be found if this path is missing.
    """
    if trial.invalid_container_path():
        msg = (f'Container path `{trial.container_path}` not present.\n'
               f'Update key `container-path` in `{trial.path.absolute()}`.')
        raise click.UsageError(click.style(msg, fg='red'))


@trial.command()
@click.argument('trial',
                type=click.Path(dir_okay=True,
                                writable=True,
                                resolve_path=True))
# FIXME: ideally are `--criteria` and `--num-patients` exclusive arguments
@click.option('-c',
              '--criteria',
              type=click.Path(exists=True),
              help="Criteria file with trial properties")
@click.option('-n', '--num-patients', type=int, default=1)
@click.option(
    '-x',
    '--dry',
    is_flag=True,
    default=False,
    help="Logs container commands to `stdout` rather than evaluating directly."
)
@click.option('-s', '--singularity', type=click.Path(exists=True))
def create(trial, criteria, num_patients, dry, singularity):
    """Create trials and their virtual cohorts.

    This creates a new in silico trial on the filesystem located at TRIAL. This
    command raises an `UsageError` if the TRIAL directory already exists and
    requires to user to either provide a different path or remove the
    conflicting directory.

    On construction the user can provide the sample size, i.e. the number of
    virtual patients to consider in the cohort, as well as to provide a the
    desired container type. By default Docker containers are used. The chosen
    container environment will be stored inside the trial's configuration.

    Once the directory for the virtual trial are set up, the
    `virtual-patient-generation` model is evaluated to sample the statistical
    model and fill the patient configuration with their properties.
    """

    # Although more convenient, the option to overwrite directories is not
    # included to prevent accidentally dropping large directories.
    if pathlib.Path(trial).exists():
        raise click.UsageError(
            click.style(f'Trial `{trial}` already exists', fg="red"))

    runner = new_runner(dry)

    # read configuration file and pass as input configuration to trial
    config = {}
    if criteria:
        config = Config.read(criteria)

    # update configuration file with provided path to Singularity containers
    if singularity:
        container_path = pathlib.Path(singularity).absolute()
        config['container-path'] = str(container_path)

    trial = Trial(trial,
                  sample_size=num_patients,
                  runner=runner,
                  config=config)
    trial.create()


@trial.command()
@click.argument('trial', type=click.Path(writable=True))
@click.option('-n', '--num', type=int)
@click.option('-x', '--dry', is_flag=True, default=False)
def append(trial, num, dry):
    """Append a number of virtual patients to the existing trial at TRIAL.

    This appends new virtual patients to an existing trial. The new patient
    directories are created, continuing with the original numbering. Again,
    the `virtual-patient-model` is evaluated, now only for the newly appended
    patients, to evaluated their statistical properties.
    """

    path = pathlib.Path(trial).joinpath(trial_config)
    trial = Trial.read(path, runner=new_runner(dry))

    # enforce container directory from configuration is valid
    assert_container_path(trial)

    # append the new patients
    sample_size = trial.get('sample_size')
    for i in range(sample_size, sample_size + num):
        trial.append_patient(i)

    # write updated trial size to configuration file, such that properties
    # are present in the `trial.yml`, as used by the virtual patient
    # generation
    trial.update({'sample_size': sample_size + num})
    trial.write()

    # evaluate the virtual patient model for the provided set of new patients
    trial.sample_virtual_patient(sample_size, sample_size + num)


@trial.command()
@click.argument('trial', type=click.Path(exists=True))
@click.option('-x', '--dry', is_flag=True, default=False)
@click.option('--parallel', is_flag=True, default=False)
@click.option(
    '--keep-files/--clean-files',
    default=True,
    help=("Keep or clean large files after evaluating all simulations."))
@click.option('--skip-completed',
              is_flag=True,
              default=False,
              help="Skip previously completed patient simulations.")
def run(trial, dry, parallel, keep_files, skip_completed):
    """Run all simulations for the patients in the in silico trial at TRIAL.

    The compute simulation pipeline is evaluated for each patient considered
    in the virtual cohort. The patients can be evaluated in parallel as well
    as sequentially. For sequential evalaution `desist` will display a simple
    progress bar in the terminal, indicating a rough estimate for the remaining
    simulation time till completion. For parallel evaluation this is disabled
    and the parallel evaluation of running the simulations is handled
    explicitly through `GNU Parallel`.

    FIXME: link documentation to example files

    """

    runner = new_runner(dry, parallel=parallel)
    config = pathlib.Path(trial).joinpath(trial_config)

    if parallel:
        trial = ParallelTrial.read(config,
                                   runner=runner,
                                   keep_files=keep_files)
    else:
        trial = Trial.read(config, runner=runner, keep_files=keep_files)

    # enforce container directory from configuration is valid
    assert_container_path(trial)

    # For parallel evaluation or when running with explicit debug logging
    # enabled, the trial is evaluated _without_ a progress bar. This prevents
    # that print statements written to the console interrupt the printing of
    # Click's progress bar.
    if parallel or logging.DEBUG >= logging.root.level:
        return trial.run(skip_completed=skip_completed)

    # Exhaust all patients in the trial's iterator within Click's progress bar.
    # This displays a basic progress bar in the terminal with ETA estimate and
    # shows the last completed patient. The patients are filtered on using
    # `skip_completed` and their `patient.completed` status to improve the ETA
    # estimate by dropping all skippable patients (this results in a more
    # accurate length of the progress bar's iterator count).
    with click.progressbar(
        [p for p in trial if not (skip_completed and p.completed)],
            show_eta=True,
            item_show_func=lambda x: f'{x.dir}' if x else None,
    ) as bar:
        for patient in bar:
            patient.run()


@trial.command()
@click.argument('trial', type=click.Path(exists=True))
@click.argument('key', type=str)
@click.option('-n', type=int, help="Lists `n` most common elements only.")
def list_key(trial, key, n):
    """Lists the values corresponding to KEY for each patient in TRIAL.

    This routine iterats all patient configurations encountered in the
    specified trial. For each configuration the provided KEY is extracted and
    its occurrences are counted for duplicate keys. By default all uniquely
    encountered values, and their count, are reported to the user.

    The `-n` option can be provided to list only the `n` most common elements
    in the list of unique elements.
    """

    # FIXME: we need to raise a usage warning for non-hashable entries, e.g.
    # lists and dicts, that cannot be placed into the `Counter` easily. Either
    # change behaviour to simply list all of them (maybe sorted?) or inform
    # the user somehow, maybe `UsageError`?

    # extract patients from trial
    config = pathlib.Path(trial).joinpath(trial_config)
    trial = Trial.read(config)

    # count occurrences of all values of `key` in patient configurations
    counter = collections.Counter([p.get(key) for p in trial])

    # ensure the sum matches the number of patients
    err = "Counted '{total=}' does not match patient count {len(patients)}"
    assert sum(counter.values()) == len(trial), err

    # report the most common keys
    click.echo(f"Encountered key '{key}' in {len(trial)} patients:")
    for (value, count) in counter.most_common(n):
        click.echo(f"'{value}' ({count})")


@trial.command()
@click.argument('trial', type=click.Path(writable=True))
def reset(trial):
    """Reset trials."""
    # FIXME: implement resetting of patients


@trial.command()
@click.argument('trial', type=click.Path(exists=True))
@click.option(
    '-x',
    '--dry',
    is_flag=True,
    default=False,
    help='Logs container commands to `stdout` rather than evaluating directly')
def outcome(trial, dry):
    """Evaluates the trial outcome model for TRIAL.

    This invokes the defined `trial_outcome_model` for the trial located
    at the provided TRIAL path on the file system.
    """

    # extract the runner and configuration
    runner = new_runner(dry)
    config = pathlib.Path(trial).joinpath(trial_config)

    # read the trial's configuration
    trial = Trial.read(config, runner=runner)
    assert_container_path(trial)

    # evaluate the outcome model
    trial.outcome()


@trial.command()
@click.argument('trial', type=click.Path(exists=True))
@click.argument('archive', type=click.Path(writable=True))
def archive(trial, archive):
    """Archive configuration file from TRIAL to ARCHIVE."""

    # prevent the files are not copied into an already populated directory
    archive = pathlib.Path(archive)
    if archive.exists():
        raise click.UsageError(
            click.style(f'Archive `{archive}` already exists', fg="red"))

    # ensure the trial can be read
    config = pathlib.Path(trial).joinpath(trial_config)
    trial = Trial.read(config)

    # prepare the archive
    archive.mkdir()

    # copy trial configuration
    shutil.copy2(trial.path, archive)

    # copy trial output if present
    for fn in ['trial_data.RData', 'trial_outcome.Rmd', 'trial_outcome.html']:
        fn = trial.dir.joinpath(fn)
        try:
            shutil.copy2(fn, archive)
        except FileNotFoundError:
            pass

    # copy directory structure for patients
    for patient in trial:
        folder = archive.joinpath(os.path.basename(patient.dir))
        folder.mkdir()

        # transfer the configuration and outcome YAML files
        for filename in ['patient.yml', 'patient_outcome.yml']:
            src = patient.dir.joinpath(filename)
            dst = folder.joinpath(filename)

            # if the file is not there, that is OK, maybe the archive call
            # is evaluated before the simulations are done, e.g. to share
            # the virtual cohort
            try:
                shutil.copy2(src, dst)
            except FileNotFoundError:
                pass
