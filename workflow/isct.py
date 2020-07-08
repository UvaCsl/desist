#!/usr/bin/env python3

"""
usage: isct [--version] [--help] <command> [<args>...]

options:
   -h, --help  Shows the usage.
   --version  Shows the version number.

The most commonly used isct commands are:
    trial     Interact with trials.
    patient   Interact with individual virtual patients.

See `isct help <command>` for more information on a specific command.
"""

from subprocess import call
from docopt import docopt
import importlib
import sys

# TODO: beforehand it is unkown which command is requested by the user.
# Therefore, the command we should run is unknown when this module is called.
# To overcome that, we dynamically load the module (which works as long as all
# the commands adhere to `workflow.isct_<command>.py`) and request the
# corresponding function name through `getattr`. Then, we simply invoke that
# script to continue operation.
def load_module(cmd):
    """Loads the module corresponding to `cmd`."""
    module = importlib.import_module(f"workflow.isct_{cmd}")
    return getattr(module, cmd)

def main(argv=None):
    # show help if no arguments are provided
    if len(sys.argv) == 1:
        sys.argv.append('-h')

    # parse the command-line arguments
    args = docopt(__doc__,
                  version="isct 0.0.1",
                  options_first=True)

    # supported commands
    valid_commands = ['trial', 'patient']

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

