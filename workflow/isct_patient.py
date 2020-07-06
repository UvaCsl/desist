"""
Usage:
    isct patient create TRIAL [--id=ID] [-f]

Arguments:
    TRIAL       Path to trial directory.

Options:
    -h, --help      Show this screen.
    --version       Show version.
    --id=ID         Identifier of the patient [default: 0].
    -f              Force overwrite exist patient directory.
"""

from docopt import docopt
from schema import Schema, Use
from pathlib import Path
import yaml
import os
import sys

def patient():
    """Provides commands for interaction with virtual patients."""
    # parse command-line arguments
    args = docopt(__doc__)

    # schema for argument validation
    schema = Schema(
            {
                '--id': Use(int, error='Only integer patient ID allowed'),
                str: object,
                }
            )

    # validate arguments
    try:
        args = schema.validate(args)
    except SchemaError as e:
        print(e)
        exit(__doc__)

    # find the configuration file
    path = Path(args['TRIAL'])
    yml = path.joinpath("trial.yml")
    patient_id = args['--id']
    overwrite = args['-f']

    # ensure configuration file exists
    if not os.path.isfile(yml):
        exit(f"No trial configuration is found in '{path}'")

    # load trial configuration
    with open(yml, "r") as outfile:
        trial_config = yaml.load(outfile, yaml.SafeLoader)

    # construct patient directory
    patient_prefix = trial_config['prefix']
    patient = path.joinpath(f"{patient_prefix}_{patient_id:03}")

    # require explicit -f to overwrite existing patient directories
    if os.path.isdir(patient) and not overwrite:
        print(f"Patient '{patient}' already exist. Provide -f to overwrite")
        exit(__doc__)

    # clear out old, existing path
    if os.path.isdir(patient):
        import shutil
        shutil.rmtree(patient)

    # setup patient directory and fill
    try:
        os.makedirs(patient)
    except OSError as e:
        exit(f"Creation of patient directory '{patient}': '{e}'")

    # TODO: this is to be filled by the `virtual_patient_generation` module
    config = {
            'id': patient_id,
            'status': False,
    }

    # write patient configuration to disk
    with open(patient.joinpath("patient.yml"), "w") as outfile:
        yaml.dump(config, outfile)


if __name__ == "__main__":
    exit(patient())
