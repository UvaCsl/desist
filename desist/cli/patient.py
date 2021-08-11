"""The subcommand for the command-line interface regarding patients."""
import click
import os
import pathlib

from .trial import assert_container_path
from desist.isct.patient import Patient, LowStoragePatient, patient_config
from desist.isct.trial import Trial, trial_config
from desist.isct.utilities import CleanFiles
import desist.isct.runner as runners


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
    '--clean-files',
    type=click.Choice([ct.value for ct in CleanFiles], case_sensitive=False),
    default=CleanFiles.NONE.value,
    help=(f"""Clean simulation files after evaluating all patient
    simulations. For \'{CleanFiles.NONE.value}\' no files are removed, this is
    the same as running without --clean-files. For \'{CleanFiles.LARGE.value}\'
    only files >1MB are removed, while \'{CleanFiles.ALL.value}\' will remove
    any file except YAML files (either \'.yml\' or \'.yaml\' suffix),
    regardless of its size."""))
@click.option('-c', '--container-path', type=click.Path(exists=True))
def run(patients, dry, clean_files, container_path):
    """Run a patient's simulation pipeline.

    The complete simulation pipeline is evaluated for the patient located
    at the provided PATIENTS path. The simulation is evaluated regardless of
    the completed flag, i.e. the simulation is _always_ invoked when
    specifically called with this command.
    """
    clean_files = CleanFiles.from_string(clean_files)

    for p in patients:
        # read patient configuration
        path = pathlib.Path(p).joinpath(patient_config)

        # define the patient type
        patient = Patient.read(path, runner=runners.new_runner(dry))

        if (clean_files != CleanFiles.NONE) and not dry:
            patient = LowStoragePatient.from_patient(patient, clean_files)

        # extract trial configuration
        trial = Trial.read(patient.dir.parent.joinpath(trial_config))

        # overwrite the container path if manually provided
        if container_path:
            trial.container_path = container_path

        # ensure the container path for singularity exists
        assert_container_path(trial)

        # only set container path if present
        patient['container-path'] = trial.container_path

        # run patient
        patient.run()


@patient.command()
@click.argument('patients', type=click.Path(exists=True), nargs=-1)
@click.option('-r',
              '--remove',
              type=click.Path(file_okay=True),
              multiple=True,
              help="Remove additional filepaths from patient directory")
def reset(patients, remove):
    """Reset the status of a patient directory.

    Predominantly resets the ``patient.completed`` property to ``False``,
    such that patients will be evaluated again in subsequent pipeline
    evaluations.
    """
    for p in patients:
        path = pathlib.Path(p).joinpath(patient_config)
        patient = Patient.read(path)
        patient.reset()

        # only drop single files
        filenames = [patient.dir.joinpath(fn) for fn in remove]
        for filepath in filter(os.path.isfile, filenames):
            filepath.unlink()
