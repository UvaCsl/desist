import click
import pathlib

from .trial import Trial, trial_config
from .patient import Patient
from .runner import new_runner
from .cli_trial import assert_container_path


@click.group()
def patient():
    """Patient"""


@patient.command()
@click.argument('patient', type=click.Path(exists=True))
@click.option('-x', '--dry', is_flag=True, default=False)
def run(patient, dry):
    """Run patients."""

    # read patient configuration
    path = pathlib.Path(patient)
    patient = Patient.read(path, runner=new_runner(dry))

    # extract trial configuration
    trial = Trial.read(patient.dir.parent.joinpath(trial_config))

    # ensure the container path for singularity exists
    assert_container_path(trial)

    # run patient
    patient |= {'container-path': trial.container_path}
    patient.run()


# @patient.command()
# @click.argument('patient', type=click.Path(exists=True))
# def reset(patient):
#     """Reset patients."""

# TODO:
# - create patient instance
# - reset patient instance
