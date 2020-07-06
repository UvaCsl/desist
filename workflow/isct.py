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

import sys

if __name__ == "__main__":
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
        exit(call(['python3', 'isct_%s.py' % args['<command>']] + argv))

    # report help for isct or specific command if given
    if args['<command>'] in ['help']:
        if len(args['<args>']) > 0:
            exit(call(['python3', 'isct_%s.py' % args['<args>'][0], "-h"]))
        else:
            exit(__doc__)

    # otherwise: invalid command
    exit("%r is not a isct command. See './isct help'." % args['<command>'])
