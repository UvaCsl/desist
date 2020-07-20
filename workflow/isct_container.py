"""
Usage:
    isct container build DIR... [-v] [-x]
    isct container run CONTAINER PATIENT ID [-v] [-x]

Arguments:
    DIR     Directory of the container to construct
    CONTAINER       Tag of the container to run
    PATIENT         Run the container for this patient directory.
    ID           The ID of the event to be evaluated.

Options:
    -h, --help      Show this screen
    --version       Show the version.
    -v              Set verbose
    -x              Dry run: only show the commands
"""

from docopt import docopt

import pathlib
import os
import sys
import schema
import shutil
import subprocess
import yaml

from workflow.patient import Patient

def get_definition_file(path):
    return path.joinpath("Dockerfile")

def form_container_exists_command(tag):
    """Returns command to evaluate to test if container with tag exists."""
    return ["docker", "image", "inspect", f"{tag}"]

# TODO: support alternative containers in addition to Docker.
def form_container_command(tag, patient, event_id):
    """Forms the Docker run command.

    Builds the command to evaluate in Docker for a given Docker tag, a given
    patient directory, and a given event_id. The command binds the corresponding
    directories towards the container and passes any required information.
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
    s = schema.Schema(
            {
                # directly validate the path
                'DIR': [schema.And(schema.Use(str), os.path.isdir)],
                str: object,
                }
        )
    try:
        args = s.validate(args)
    except schema.SchemaError as e:
        # report validation errors before exiting
        print(e)
        sys.exit(__doc__)

    # verbosity
    dry_run = args['-x']
    verbose = True if dry_run else args['-v']

    # if docker is not present, perform a dry drun
    if shutil.which("docker") is None:
        print("Docker executable is not present. Performs a dry run.")
        verbose = True
        dry_run = True

    # create path
    dirs = [pathlib.Path(d) for d in args['DIR']]

    for d in dirs:
        # FIXME: not explicitly required at the moment
        definition = get_definition_file(d)

        # container name equal to its directory
        tag = os.path.basename(d)
        cmd = ["docker", "build", str(d.absolute()), "-t", tag]

        # show the command
        if verbose:
            print(" + " + " ".join(cmd))

        # evaluate the command
        if not dry_run:
            subprocess.run(cmd)

def run_container(args):
    """Runs the container of the provided tag for the given patient."""

    # validate arguments:
    #   container is string
    #   patient a valid path
    #   event ID is positive integer
    s = schema.Schema(
            {
                'CONTAINER': schema.Use(str),
                'PATIENT': schema.And(schema.Use(str), os.path.isdir),
                'ID': schema.And(schema.Use(int), lambda n: n >= 0),
                str: object,
            }
        )
    try:
        args = s.validate(args)
    except schema.SchemaError as e:
        print(e)
        sys.exit(__doc__)

    # test if docker exists
    if shutil.which("docker") is None:
        print("Docker executable not present.")
        sys.exit(__doc__)

    # verbosity and/or dry run
    dry_run = args['-x']
    verbose = True if dry_run else args['-v']

    # ensure the container exists
    tag = args['CONTAINER']
    p_dir = args['PATIENT']
    event_id = args['ID']
    cmd = form_container_exists_command(tag)

    if verbose:
        print(" + " + " ".join(cmd))

    if not dry_run:
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e :
            print(f'Container does not exit: "{e}"')
            return

    # assert tag and event match: an event exists with the provided ID
    patient = Patient.from_yaml(p_dir)

    match_event_id = False
    for event in patient.events():
        if event['event'] == tag and event['id'] == event_id:
            match_event_id = True

    msg = f"No match found for tag: '{tag}' and id: '{event_id}'."
    assert match_event_id, msg

    # evaluate the docker of that tag with the files
    cmd = form_container_command(tag, patient.dir, args['ID'])

    # logging
    if verbose:
        print(" + " + " ".join(cmd))

    # evaluation
    if not dry_run:
        subprocess.run(cmd)

        # mark event as complete and update config file on disk
        patient.completed_event(event_id)
        patient.to_yaml()


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

