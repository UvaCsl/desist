"""
Usage:
    isct container build DIR... [-v] [-x]

Arguments:
    DIR     Directory of the container to construct

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

def get_definition_file(path):
    return path.joinpath("Dockerfile")

def container(argv=None):
    """Provides commands for interaction with building containers."""
    # show `-h` when no arguments are given
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) == 0:
        argv = ['-h']

    # parse command-line arguments
    args = docopt(__doc__, argv=argv, version="0.0.1")

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
            subprocess.call(cmd)

if __name__ == "__main__":
    sys.exit(container(sys.argv[1:]))

