"""
Usage:
    isct patient create TRIAL [--id=ID] [-f] [--seed=SEED] [--config-only]
    isct patient run PATIENT [-x] [-v]

Arguments:
    TRIAL       Path to trial directory.
    PATIENT     Path to a patient's directory.

Options:
    -h, --help      Show this screen.
    --version       Show version.
    --id=ID         Identifier of the patient [default: 0].
    -f              Force overwrite exist patient directory.
    --seed=SEED     Random seed for the patient generation [default: 1].
    --config-only   Only generate a patient configuration file, and do not
                    invoke the `virtual_patient_generation` module.
    -x              Perform a dry run: show commands to be executed without
                    executing these commands.
    -v              Set output verbosity.
"""

from docopt import docopt
from schema import Schema, Use, SchemaError
from subprocess import call
import pathlib
import schema
import yaml
import os
import sys
import random

from workflow.isct_container import container as container_cmd
from workflow.patient import Patient

def patient_create(args):
    """Provides `patient create` to creating individual patients."""
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
    path = pathlib.Path(args['TRIAL'])
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

    # initialise the Patient
    patient = Patient(path.joinpath(f"{patient_prefix}_{patient_postfix}"))

    # require explicit -f to overwrite existing patient directories
    if os.path.isdir(patient.dir) and not overwrite:
        print(f"Patient '{patient}' already exist. Provide -f to overwrite")
        sys.exit(__doc__)

    # clear out old, existing path
    if os.path.isdir(patient.dir):
        import shutil
        shutil.rmtree(patient.dir)

    # setup patient directory and fill
    os.makedirs(patient.dir, exist_ok=True)

    # seed the random generator with the provided seed
    random.seed(seed)

    # pull the n-th random number, for the n-th patient
    for i in range(patient_id+1):
       p_seed = random.randrange(2<<31 - 1)

    # set basic configruation
    patient.set_defaults(patient_id, p_seed)

    # write patient configuration to disk
    patient.to_yaml()

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

    # events are added _after_ `virtrual_patient_generation` to allow for the
    # possibility of adding logic in the events, e.g. if age > criteria then
    # assume a different event chain

    # read the config back, add events, and write back to disk
    patient = Patient.from_yaml(patient.full_path())
    patient.set_events(overwrite=True)
    patient.to_yaml()
    patient.to_xml()

def patient_run(argv):
    """Evaluate `patient run` to process the patient's events."""

    # validate the provided path exists
    s = schema.Schema(
            {
                'PATIENT': schema.And(schema.Use(str), os.path.isdir),
                str: object,
            }
        )
    try:
        args = s.validate(argv)
    except schema.SchemaError as e:
        print(e)
        sys.exit(__doc__)

    # obtain patient configuration
    path = pathlib.Path(args['PATIENT'])
    with open(path.joinpath("patient.yml"), "r") as configfile:
        config = yaml.load(configfile, yaml.SafeLoader)

    dry_run = args['-x']
    verbose = True if dry_run else args['-v']

    # run through all events
    for i, event in enumerate(config['events']):

        # ensure we traverse events in the correct order
        assert i == event['id']

        cmd = ["container", "run", event['event'], str(path.absolute()), str(event['id'])]

        if dry_run:
            cmd += ["-x"]

        if verbose:
            cmd += ["-v"]

        container_cmd(cmd)

    return

def patient(argv):
    """Provides commands for interaction with virtual patients."""
    # parse command-line arguments
    args = docopt(__doc__, argv=argv)

    if args['create']:
        return patient_create(args)

    if args['run']:
        return patient_run(args)


if __name__ == "__main__":
    sys.exit(patient(sys.argv[1:]))
