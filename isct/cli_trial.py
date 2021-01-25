import click
import pathlib

from .trial import Trial, ParallelTrial, trial_config
from .runner import new_runner

# FIXME: add `trial status` to show current status of the problem


@click.group()
def trial():
    """Trial"""


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
def create(trial, num_patients, dry):
    """Create trials."""

    # Although more convenient, the option to overwrite directories is not
    # included to prevent accidentally dropping large directories.
    # FIXME: consider adding user-based confirmation to overwrite?
    if pathlib.Path(trial).exists():
        raise click.UsageError(
            click.style(f'Trial `{trial}` already exists', fg="red"))

    runner = new_runner(dry)
    trial = Trial(trial, sample_size=num_patients, runner=runner)
    trial.create()


@trial.command()
@click.argument('trial', type=click.Path(writable=True))
@click.option('-n', '--num', type=int)
@click.option('-x', '--dry', is_flag=True, default=False)
def append(trial, num, dry):
    """Append patient to existing trial."""

    path = pathlib.Path(trial).joinpath(trial_config)
    trial = Trial.read(path, runner=new_runner(dry))

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

    if parallel:
        trial = ParallelTrial(trial, runner=runner)
    else:
        trial = Trial(trial, runner=runner)

    trial.run()


@trial.command()
@click.argument('trial', type=click.Path(writable=True))
def reset(trial):
    """Reset trials."""
    # FIXME: implement resetting of patients
