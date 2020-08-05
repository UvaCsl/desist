"""
Usage:
    isct patient create TRIAL [--id=ID] [-f] [--seed=SEED] [--config-only] [--singularity=DIR]
    isct patient run PATIENT [-x] [-v] [--singularity=DIR]

Arguments:
    TRIAL       Path to a trial directory.
    PATIENT     Path to a patient directory.
    DIR         Path to a directory containing the Singularity images.

Options:
    -h, --help                  Shows the usage of `isct patient`.
    --version                   Show the version number.
    --id=ID                     Identifier of the patient [default: 0].
    -f                          Force overwrite exist patient directory.
    --seed=SEED                 Random seed for the patient generation [default: 1].
    --config-only               Only generate a patient configuration file, and do not
                                invoke the `virtual_patient_generation` module.
    -x                          Perform a dry run: show commands to be executed without
                                executing these commands.
    -v                          Set output verbosity.
    -s, --singularity=DIR       Use Singularity rather than Docker by providing the
                                directory `DIR` containing the Singularity images.
"""

from docopt import docopt
import logging
import subprocess
import pathlib
import schema
import yaml
import os
import sys
import random
import shutil

from workflow.container import new_container
from workflow.isct_container import container as container_cmd
from workflow.patient import Patient

def patient_create(args):
    """Provides `patient create` to creating individual patients."""
    # schema for argument validation
    s = schema.Schema(
            {
                '--id': schema.Use(int, error='Only integer patient ID allowed'),
                '--seed': schema.Use(int, error='Only integer random seeds allowed'),
                '--singularity': schema.Or(None, schema.And(schema.Use(str), os.path.isdir)),
                str: object,
                }
            )

    # validate arguments
    try:
        args = s.validate(args)
    except schema.SchemaError as e:
        logging.critical(e)
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
        logging.critical(f"Patient '{patient.dir}' already exist. Provide -f to overwrite")
        sys.exit(__doc__)

    # clear out old, existing path
    if os.path.isdir(patient.dir):
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

    c = new_container(args['--singularity'])

    # only call docker to fill the patients data when not set
    if not args['--config-only']:
        tag = "virtual_patient_generation"
        arg = f"/patients/{patient_prefix}_{patient_postfix}"

        c.bind_volume(path.absolute(), "/patients/")
        cmd = c.run_image(tag, arg)

        # only call into Docker when available on the system
        if not c.executable_present():
            logging.warning(f"Cannot reach {c.type}.")
            return

        subprocess.run(cmd)

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
                '--singularity': schema.Or(None, schema.And(schema.Use(str), os.path.isdir)),
                str: object,
            }
        )
    try:
        args = s.validate(argv)
    except schema.SchemaError as e:
        logging.critical(e)
        sys.exit(__doc__)

    # process arguments
    patient = Patient.from_yaml(args['PATIENT'])
    dry_run = args['-x']
    verbose = True if dry_run else args['-v']

    # run through all events
    for i, event in enumerate(patient.events()):

        # ensure we traverse events in the correct order
        assert i == event['id']

        cmd = ["container", "run", event['event'], str(patient.dir), str(event['id'])]

        if dry_run:
            cmd += ["-x"]

        if verbose:
            cmd += ["-v"]

        if args['--singularity'] is not None:
            cmd += ["--singularity", args['--singularity']]

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
