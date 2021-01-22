import click
import pathlib

from .patient import Patient, patient_config


@click.group()
def patient():
    """Patient"""


@patient.command()
@click.argument('patient', type=click.Path(exists=True))
def run(patient):
    """Run patients."""

    # TODO:
    # - create patient instance
    # - run patient instance

    path = pathlib.Path(patient).joinpath(patient_config)
    patient = Patient.read(path)
    patient.run()


# @patient.command()
# @click.argument('patient', type=click.Path(exists=True))
# def reset(patient):
#     """Reset patients."""

    # TODO:
    # - create patient instance
    # - reset patient instance
