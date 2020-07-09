"""
Usage:
    isct patient create TRIAL [--id=ID] [-f] [--seed=SEED] [--config-only]

Arguments:
    TRIAL       Path to trial directory.

Options:
    -h, --help      Show this screen.
    --version       Show version.
    --id=ID         Identifier of the patient [default: 0].
    -f              Force overwrite exist patient directory.
    --seed=SEED     Random seed for the patient generation [default: 1].
    --config-only   Only generate a patient configuration file, and do not
                    invoke the `virtual_patient_generation` module.
"""

from docopt import docopt
from schema import Schema, Use, SchemaError
from pathlib import Path
from subprocess import call
import yaml
import os
import sys
import random

def patient(argv):
    """Provides commands for interaction with virtual patients."""
    # parse command-line arguments
    args = docopt(__doc__, argv=argv)

    # schema for argument validation
    schema = Schema(
            {
                '--id': Use(int, error='Only integer patient ID allowed'),
                '--seed': Use(int, error='Only integer random seeds allowed'),
                str: object,
                }
            )

    # validate arguments
    try:
        args = schema.validate(args)
    except SchemaError as e:
        print(e)
        sys.exit(__doc__)

    # find the configuration file
    path = Path(args['TRIAL'])
    yml = path.joinpath("trial.yml")
    patient_id = args['--id']
    overwrite = args['-f']
    seed = args['--seed']

    # ensure configuration file exists
    if not os.path.isfile(yml):
        sys.exit(f"No trial configuration is found in '{path}'")

    # load trial configuration
    with open(yml, "r") as outfile:
        trial_config = yaml.load(outfile, yaml.SafeLoader)

    # construct patient directory
    patient_prefix = trial_config['prefix']
    patient_postfix = f"{patient_id:03}"
    patient = path.joinpath(f"{patient_prefix}_{patient_postfix}")

    # require explicit -f to overwrite existing patient directories
    if os.path.isdir(patient) and not overwrite:
        print(f"Patient '{patient}' already exist. Provide -f to overwrite")
        sys.exit(__doc__)

    # clear out old, existing path
    if os.path.isdir(patient):
        import shutil
        shutil.rmtree(patient)

    # setup patient directory and fill
    os.makedirs(patient, exist_ok=True)

    # seed the random generator with the provided seed
    random.seed(seed)

    # pull the n-th random number, for the n-th patient
    for i in range(patient_id+1):
       p_seed = random.randrange(sys.maxsize)

    # TODO: this is to be filled by the `virtual_patient_generation` module
    config = {
            'id': patient_id,
            'status': False,
            'random_seed': p_seed,
    }

    # write patient configuration to disk
    with open(patient.joinpath("patient.yml"), "w") as outfile:
        yaml.dump(config, outfile)

    # only call docker to fill the patients data when not set
    if not args['--config-only']:
        cmd = [
                "docker",
                "run", "-v", f"{path.absolute()}:/patients/",
                "virtual_patient_generation",
                f"/patients/{patient_prefix}_{patient_postfix}"
        ]

        # only call into Docker when available on the system
        if shutil.which("docker") is None:
            print("Cannot reach Docker.")
            return

        call(cmd)

if __name__ == "__main__":
    sys.exit(patient(sys.argv[1:]))
