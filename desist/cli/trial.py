"""The subcommand for the command-line interface regarding trials."""

import click
import collections
import logging
import os
import pathlib
import shutil

from desist.isct.config import Config
from desist.isct.trial import Trial, ParallelTrial, trial_config
from desist.isct.runner import new_runner


@click.group()
def trial():
    """The trial subcommand.

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
@click.option(
    '-s',
    '--singularity',
    type=click.Path(exists=True),
    help=(
        "Use Singularity-based container images. "
        "The Sigularity container images are obtained from the provided path.")
)
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
@click.option(
    '-c',
    '--container-path',
    type=click.Path(exists=True, resolve_path=True),
    help="Override the container path as defined in the trial configuration")
def run(trial, dry, parallel, keep_files, skip_completed, container_path):
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

    cls = ParallelTrial if parallel else Trial
    try:
        trial = cls.read(config, runner=runner, keep_files=keep_files)
    except (FileNotFoundError, IsADirectoryError):
        # If parsing the trial fails due to missing `trial.yml` configuration,
        # we can still attempt to fallback on creating a trial in the
        # configurations' parent directory, i.e. the directory of the trial.
        # In this case, we have _no_ information whatsoever on the properties
        # of the trial, basically all configuration is either missing or is
        # set to the default values of the trials. However, the methods to
        # extract patients within a trial will simply look at the available
        # subdirectories. If those are valid patients, the subsequent run
        # instructions will work as usual, as those can pull all their
        # configuration data from the `trial/patient_*/patient.yml` files.
        #
        # Thus, the package does not need to terminate on this error, as we
        # can attempt to recover. This is for instance of use when sets of
        # patients are moved in to other directories, or that patients are
        # generated without specific trial information, such as is commonly
        # done when performing VVUQ analysis.
        trial = cls(path=config.parent, runner=runner, keep_files=keep_files)

    # overwrite the container path when provided as argument
    if container_path:
        trial.container_path = container_path

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

    Note: here it is assumed the provided key is ``Hashable`` and can be
    counted within the dictionary. This excludes nested dictionaries or lists
    at the moment.

    The `-n` option can be provided to list only the `n` most common elements
    in the list of unique elements.
    """
    # extract patients from trial
    config = pathlib.Path(trial).joinpath(trial_config)
    trial = Trial.read(config)

    # count occurrences of all values of `key` in patient configurations
    occurrences = [p.get(key) for p in trial]
    try:
        counter = collections.Counter(occurrences)
    except TypeError:
        key_type = type(occurrences[0])
        msg = (f'Key `{key}` cannot be listed.\n'
               f'The entry is of type: `{key_type}`, currently not supported')
        raise click.UsageError(click.style(msg, fg="red"))

    # ensure the sum matches the number of patients
    err = "Counted '{total=}' does not match patient count {len(patients)}"
    assert sum(counter.values()) == len(trial), err

    # report the most common keys
    click.echo(f"Encountered key '{key}' in {len(trial)} patients:")
    for (value, count) in counter.most_common(n):
        click.echo(f"'{value}' ({count})")


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
@click.option('-a',
              '--add',
              type=click.Path(file_okay=True),
              multiple=True,
              help="Add files to extract from each patient directory")
def archive(trial, archive, add):
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

    # the files to be extracted from each patient directory: `trial/patient_*/`
    outfiles = ['patient.yml', 'patient_outcome.yml']
    if add:
        outfiles.extend(add)

    # copy directory structure for patients
    for patient in trial:
        folder = archive.joinpath(os.path.basename(patient.dir))
        folder.mkdir()

        # transfer the configuration and outcome YAML files
        for filename in outfiles:
            src = patient.dir.joinpath(filename)
            dst = folder.joinpath(filename)

            # ensure the folder is present on the archive
            os.makedirs(dst.parent, exist_ok=True)

            # if the file is not there, that is OK, maybe the archive call
            # is evaluated before the simulations are done, e.g. to share
            # the virtual cohort
            try:
                shutil.copy2(src, dst)
            except FileNotFoundError:
                pass


@trial.command()
@click.argument('trial', type=click.Path(exists=True))
@click.option('-r',
              '--remove',
              type=click.Path(file_okay=True),
              multiple=True,
              help="Remove additional filepaths from patient directory")
def reset(trial, remove):
    """Reset all patient directories of the trial.

    Specifically, the ``patient.completed`` flags are reset for all patients
    present in the trial. Additionally, the specified files with `-r, --remove`
    are removed from each patient directory as well. This can be used to
    remove specific simulation files throughout all patient directories.

    >>> isct trial reset $trial --remove Clots.txt
    # deletes $trial/patient_*/Clots.txt
    """
    # ensure the trial can be read
    config = pathlib.Path(trial).joinpath(trial_config)
    trial = Trial.read(config)

    for patient in trial:
        patient.reset()

        filenames = [patient.dir.joinpath(fn) for fn in remove]
        for filepath in filter(os.path.isfile, filenames):
            filepath.unlink()
