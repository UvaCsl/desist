import click
import pathlib

from .patient import Patient
from .runner import create_runner


@click.group()
def patient():
    """Patient"""


@patient.command()
@click.argument('patient', type=click.Path(exists=True))
@click.option('-x', '--dry', is_flag=True, default=False)
def run(patient, dry):
    """Run patients."""

    path = pathlib.Path(patient)
    patient = Patient.read(path, runner=create_runner(dry))
    patient.run()


# @patient.command()
# @click.argument('patient', type=click.Path(exists=True))
# def reset(patient):
#     """Reset patients."""

    # TODO:
    # - create patient instance
    # - reset patient instance
