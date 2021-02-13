import click
import pathlib

from .trial import Trial, trial_config
from .patient import Patient
from .runner import new_runner
from .cli_trial import assert_container_path


@click.group()
def patient():
    """Patient

    The `patient` command provides commands to interact with specific patients
    present in an in silico computational trial.
    """


@patient.command()
@click.argument('patient', type=click.Path(exists=True))
@click.option('-x', '--dry', is_flag=True, default=False)
def run(patient, dry):
    """Run a patient's simulation pipeline.

    The complete simulation pipeline is evaluated for the patient located
    at the provided PATIENT path. The simulation is evaluated regardless of
    the completed flag, i.e. the simulation is _always_ invoked when
    specifically called with this command.
    """

    # read patient configuration
    path = pathlib.Path(patient)
    patient = Patient.read(path, runner=new_runner(dry))

    # extract trial configuration
    trial = Trial.read(patient.dir.parent.joinpath(trial_config))

    # ensure the container path for singularity exists
    assert_container_path(trial)

    # only set container path if present
    patient |= {'container-path': trial.container_path}

    # run patient
    patient.run()


# @patient.command()
# @click.argument('patient', type=click.Path(exists=True))
# def reset(patient):
#     """Reset patients."""

# FIXME:
# - create patient instance
# - reset patient instance
