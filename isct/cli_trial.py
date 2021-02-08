import click
import logging
import pathlib

from .trial import Trial, ParallelTrial, trial_config
from .runner import new_runner

# FIXME: add `trial status` to show current status of the problem


@click.group()
def trial():
    """Trial"""


def assert_container_path(trial):
    if trial.invalid_container_path():
        msg = (f'Container path `{trial.container_path}` not present.\n'
               f'Update key `container-path` in `{trial.path.absolute()}`.')
        raise click.UsageError(click.style(msg, fg='red'))


@trial.command()
@click.argument('trial',
                type=click.Path(dir_okay=True,
                                writable=True,
                                resolve_path=True))
@click.option('-n', '--num-patients', type=int, default=1)
@click.option(
    '-x',
    '--dry',
    is_flag=True,
    default=False,
    help="Logs container commands to `stdout` rather than evaluating directly."
)
@click.option('-s', '--singularity', type=click.Path(exists=True))
def create(trial, num_patients, dry, singularity):
    """Create trials."""

    # Although more convenient, the option to overwrite directories is not
    # included to prevent accidentally dropping large directories.
    if pathlib.Path(trial).exists():
        raise click.UsageError(
            click.style(f'Trial `{trial}` already exists', fg="red"))

    runner = new_runner(dry)
    config = {}

    # update configuration file with provided path to Singularity containers
    if singularity:
        container_path = pathlib.Path(singularity).absolute()
        config = {'container-path': str(container_path)}

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
    """Append patient to existing trial."""

    path = pathlib.Path(trial).joinpath(trial_config)
    trial = Trial.read(path, runner=new_runner(dry))

    # enforce container directory from configuration is valid
    assert_container_path(trial)

    sample_size = trial.get('sample_size')
    for i in range(sample_size, sample_size + num):
        trial.append_patient(i)

    trial.sample_virtual_patient(sample_size, sample_size + num)
    trial.update({'sample_size': sample_size + num})
    trial.write()


@trial.command()
@click.argument('trial', type=click.Path(exists=True))
@click.option('-x', '--dry', is_flag=True, default=False)
@click.option('--parallel', is_flag=True, default=False)
def run(trial, dry, parallel):
    """Run trials."""

    runner = new_runner(dry, parallel=parallel)
    config = pathlib.Path(trial).joinpath(trial_config)

    if parallel:
        trial = ParallelTrial.read(config, runner=runner)
    else:
        trial = Trial.read(config, runner=runner)

    # enforce container directory from configuration is valid
    assert_container_path(trial)

    # For parallel evaluation or when running with explicit debug logging
    # enabled, the trial is evaluated _without_ a progress bar. This prevents
    # that print statements written to the console interrupt the printing of
    # Click's progress bar.
    if parallel or logging.DEBUG >= logging.root.level:
        return trial.run()

    # Exhaust all patients in the trial's iterator within Click's progress bar.
    # This displays a basic progress bar in the terminal with ETA estimate and
    # shows the last completed patient.
    with click.progressbar(
            trial,
            show_eta=True,
            item_show_func=lambda x: f'{x.dir}' if x else None,
    ) as bar:
        for patient in bar:
            patient.run()


@trial.command()
@click.argument('trial', type=click.Path(writable=True))
def reset(trial):
    """Reset trials."""
    # FIXME: implement resetting of patients
