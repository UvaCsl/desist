"""The subcommand for the command-line interface regarding patients."""
import click
import pathlib

from .trial import Trial, trial_config
from .patient import Patient, LowStoragePatient, patient_config
from .runner import new_runner
from .cli_trial import assert_container_path


@click.group()
def patient():
    """The patient subcommand.

    The `patient` command provides commands to interact with specific patients
    present in an in silico computational trial.
    """


@patient.command()
@click.argument('patients', type=click.Path(exists=True), nargs=-1)
@click.option('-x', '--dry', is_flag=True, default=False)
@click.option(
    '--keep-files/--clean-files',
    default=True,
    help=("Keep or clean large files after evaluating all simulations."))
def run(patients, dry, keep_files):
    """Run a patient's simulation pipeline.

    The complete simulation pipeline is evaluated for the patient located
    at the provided PATIENTS path. The simulation is evaluated regardless of
    the completed flag, i.e. the simulation is _always_ invoked when
    specifically called with this command.
    """
    for p in patients:
        # read patient configuration
        path = pathlib.Path(p).joinpath(patient_config)

        # define the patient type
        patient = Patient.read(path, runner=new_runner(dry))

        if not keep_files:
            patient = LowStoragePatient.from_patient(patient)

        # extract trial configuration
        trial = Trial.read(patient.dir.parent.joinpath(trial_config))

        # ensure the container path for singularity exists
        assert_container_path(trial)

        # only set container path if present
        patient['container-path'] = trial.container_path

        # run patient
        patient.run()


# @patient.command()
# @click.argument('patient', type=click.Path(exists=True))
# def reset(patient):
#     """Reset patients."""

# FIXME:
# - create patient instance
# - reset patient instance
