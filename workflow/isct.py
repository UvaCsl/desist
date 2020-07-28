#!/usr/bin/env python3

"""
usage: isct [--version] [--help] [--log=<path>] <command> [<args>...]

options:
   -h, --help       Shows the usage.
   --version        Shows the version number.
   --log=<path>     Path to store the logfile [default: /tmp/isct.log].

The most commonly used isct commands are:
    container Interact with Docker/Singularity containers of event modules.
    patient   Interact with individual virtual patients.
    trial     Interact with trials.

See `isct help <command>` for more information on a specific command.
"""

from docopt import docopt, DocoptExit
import importlib
import logging, logging.handlers
import pathlib
import os
import sys
import schema

# Beforehand it is unkown which command is requested by the user. Therefore,
# the command we should run is unknown when this module is called. To overcome
# that, we dynamically load the module (which works as long as all the commands
# adhere to `workflow.isct_<command>.py`) and request the corresponding
# function name through `getattr`. Then, we simply invoke that script to
# continue operation.
def load_module(cmd):
    """Loads the module corresponding to `cmd`."""
    module = importlib.import_module(f"workflow.isct_{cmd}")
    return getattr(module, cmd)

def main(argv=None):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # create a console handler logging from warning and higher
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    logger.addHandler(ch)

    argv = sys.argv[1:] if argv is None else argv
    if len(argv) == 0:
        argv.append('-h')

    # parse the command-line arguments
    args = docopt(__doc__,
                  version="isct 0.0.1",
                  options_first=True,
                  argv=argv)

    # ensure the path for the log file (`--log`) is an existing directory
    s = schema.Schema(
            {'--log': schema.And(
                schema.Use(str),
                lambda p: os.path.isdir(pathlib.Path(p).parent) is True,
                error='Invalid path for logfile.'),
            str: object,
                })
    try:
        args = s.validate(args)
    except schema.SchemaError as e:
        logging.critical(e)
        exit(__doc__)

    # Setup a rotating file handler at the indicated log file location. The
    # logfile is given a maximum size of ~1MB before it rotates.
    fh = logging.handlers.RotatingFileHandler(args['--log'], maxBytes=1000000, backupCount=5)
    fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(fh)

    # store the invoked, validated arguments
    logging.debug(f'Invoked `isct` with args: {args}')

    # supported commands
    valid_commands = ['trial', 'patient', 'container']

    # complete arguments to pass
    argv = [args['<command>']] + args['<args>']

    # run specific command's interface
    if args['<command>'] in valid_commands:
        f = load_module(args['<command>'])
        return f(argv)

    # report help for isct or specific command if given
    if args['<command>'] in ['help']:
        if len(args['<args>']) > 0:
            f = load_module(args['<args>'][0])
            return f(['-h'])
        else:
            sys.exit(__doc__)

    # otherwise: invalid command
    sys.exit("%r is not a isct command. See './isct help'." % args['<command>'])

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

