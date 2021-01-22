import click
import pathlib

from .trial import Trial, trial_config
from .runner import create_runner


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
@click.option('-x', '--dry', is_flag=True, default=False)
def create(trial, num_patients, dry):
    """Create trials."""

    # FIXME: insert warning if directory already exists
    # FIXME: provide argument that allows for overwriting or not?
    #        it might be nicer to avoid the `os.unlink` of complete
    #        directories, just to prevent accidental dropping

    runner = create_runner(dry)
    trial = Trial(trial, sample_size=num_patients, runner=runner)
    trial.create()


@trial.command()
@click.argument('trial', type=click.Path(writable=True))
@click.option('-n', '--num', type=int)
@click.option('-x', '--dry', is_flag=True, default=False)
def append(trial, num, dry):
    """Append patient to existing trial."""

    path = pathlib.Path(trial).joinpath(trial_config)
    trial = Trial.read(path)

    # FIXME: insert the `runner` more elegantly into the trial
    trial.runner = create_runner(dry)

    sample_size = trial.get('sample_size')
    for i in range(sample_size, sample_size + num):
        trial.append_patient(i)

    trial.sample_virtual_patient(sample_size, sample_size + num)
    trial.update({'sample_size': sample_size + num})
    trial.write()


@trial.command()
@click.argument('trial', type=click.Path(exists=True))
@click.option('-x', '--dry', is_flag=True, default=False)
def run(trial, dry):
    """Run trials."""
    trial = Trial(trial)
    trial.runner = create_runner(dry)
    trial.run()


@trial.command()
@click.argument('trial', type=click.Path(writable=True))
def reset(trial):
    """Reset trials."""
    # FIXME: implement resetting of patients
