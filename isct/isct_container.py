"""
Usage:
    isct container build DIR... [-v] [-x] [--singularity=PATH] [--gnu-parallel]
                        [--root]
    isct container run CONTAINER PATIENT ID [-v] [-x] [--singularity=PATH]
                        [--root]

Arguments:
    DIR             Directory of the container to construct.
    CONTAINER       Tag of the container to run.
    PATIENT         Run the container for this patient directory.
    ID              The ID of the event to be evaluated.
    PATH            The path containing the singularity images.

Options:
    -h, --help                  Show the usage of `isct container`.
    --version                   Show the version number.
    -v                          Set verbose output.
    -x                          Dry run: only show commands.
    -s, --singularity=PATH      Use `Singularity` to build the containers.
    --gnu-parallel              Output commands over `stdout` to be piped into
                                `GNU parallel`, e.g. `isct trial run
                                TRIAL --gnu-parallel | parallel -j+0`.
    --root                      Indicates the user has root permissions and
                                no `sudo` has be prefixed for Docker
                                containers.
"""

from docopt import docopt

import logging
import pathlib
import os
import sys
import schema

from .container import new_container
from .patient import Patient
import isct.utilities as utilities


# TODO: support alternative containers in addition to Docker.
def form_container_command(tag, patient, event_id):
    """Forms the Docker run command.

    Builds the command to evaluate in Docker for a given Docker tag, a given
    patient directory, and a given event_id. The command binds the
    corresponding directories towards the container and passes any required
    information.
    """
    cmd = ["docker", "run"]

    # add the bind mounts
    cmd += ["-v"]
    path = pathlib.Path(patient).absolute()
    cmd += [f"{path}:/patient"]

    # add the container to run
    cmd += [f"{tag}"]

    # add events
    cmd += ["handle_event", "--patient=/patient/config.xml"]
    cmd += ["--event", f"{event_id}"]

    return cmd


def build_container(args):
    """Construct the containers."""
    # validate arguments: ensure valid _and_ existing paths
    s = schema.Schema({
        # directly validate the path
        'DIR': [schema.And(schema.Use(str), os.path.exists)],
        '--singularity':
        schema.Or(None, schema.And(schema.Use(str), os.path.isdir)),
        '--gnu-parallel':
        bool,
        '--root':
        schema.Use(bool),
        str:
        object,
    })
    try:
        args = s.validate(args)
    except schema.SchemaError as e:
        # report validation errors before exiting
        logging.critical(e)
        sys.exit(__doc__)

    # verbosity
    c = new_container(args['--singularity'], args['--root'])
    dry_run = True if c.dry_run() else args['-x']
    verbose = True if dry_run else args['-v']
    gnu_parallel = args['--gnu-parallel']

    if verbose:
        logging.getLogger().handlers[0].setLevel(logging.INFO)

    # get the absolute path of the containers and filter out any non-directory
    paths = map(lambda p: pathlib.Path(p).absolute(), args['DIR'])
    dirs = list(filter(os.path.isdir, paths))

    for d in dirs:
        # obtain the command to build the container
        cmd = " ".join(c.build_image(d))

        # only pipe the command into `stdout` for parallel evaluation
        if gnu_parallel:
            logging.info(" + " + cmd)
            sys.stdout.write(f'{cmd}\n')
            continue

        # evaluate the command
        if not dry_run:
            utilities.run_and_stream(cmd, logging, shell=True)


def run_container(args):
    """Runs the container of the provided tag for the given patient."""

    # validate arguments:
    #   container is string
    #   patient a valid path
    #   event ID is positive integer
    s = schema.Schema({
        'CONTAINER':
        schema.Use(str),
        'PATIENT':
        schema.And(schema.Use(str), os.path.isdir),
        'ID':
        schema.And(schema.Use(int), lambda n: n >= 0),
        '--singularity':
        schema.Or(None, schema.And(schema.Use(str), os.path.isdir)),
        '--root':
        schema.Use(bool),
        str:
        object,
    })
    try:
        args = s.validate(args)
    except schema.SchemaError as e:
        logging.critical(e)
        sys.exit(__doc__)

    # create container and set verbosity
    c = new_container(args['--singularity'], args['--root'])
    dry_run = True if c.dry_run() else args['-x']
    verbose = True if dry_run else args['-v']
    if verbose:
        logging.getLogger().handlers[0].setLevel(logging.INFO)

    # ensure the container exists
    tag = args['CONTAINER']
    p_dir = args['PATIENT']
    event_id = args['ID']

    # assert the considered container exists
    if not c.executable_present():
        sys.exit(1)

    # ensure the container image is present
    if not c.image_exists(tag, dry_run):
        sys.exit(1)

    # assert tag and event match: an event exists with the provided ID
    patient = Patient.from_yaml(p_dir)
    msg = f"No match found for tag: '{tag}' and id: '{event_id}'."
    assert patient.match_tag_id(tag, event_id), msg

    # bind the patient directory to the container
    c.bind_volume(patient.dir, "/patient")

    # construct the container command with the desired arguments
    inp = f"event -p /patient/ -e {args['ID']}"
    cmd = c.run_image(tag, inp)

    if patient.terminated:
        logging.critical(
            "Patient has been flagged as terminated due to previous errors.\n"
            "Skipping container execution")

    if not dry_run and not patient.terminated:

        # evaluate command and stream its output to the logger
        returncode = utilities.run_and_stream(cmd, logging)

        # mark event as complete for successful evaluation
        if returncode == 0:
            patient.completed_model(event_id)
        else:
            logging.critical(f"Container failed with exit code '{returncode}'")
            logging.critical("Flagging patient to be terminated...")
            patient.terminate()

        # update config file on disk
        patient.to_yaml()

    # update file permissions
    c.set_permissions(patient.dir, tag, dry_run)


def container(argv=None):
    """Provides commands for interaction with building containers."""
    # show `-h` when no arguments are given
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) == 0:
        argv = ['-h']

    # parse command-line arguments
    args = docopt(__doc__, argv=argv, version="0.0.1")

    if args['build']:
        build_container(args)
        return

    if args['run']:
        run_container(args)
        return


if __name__ == "__main__":
    sys.exit(container(sys.argv[1:]))
