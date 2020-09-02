#!/usr/bin/env python3
"""
Usage: isct [--version] [--help] [--log=<path>] <command> [<args>...]

Options:
   -h, --help       Shows the usage of the `isct` command.
   --version        Shows the version number.
   --log=<path>     Path to store the logfile [default: /tmp/isct.log].

The most commonly used `isct` commands are:
    container   Interact with Docker/Singularity containers of event modules.
    help        Show help for any of the commands.
    patient     Interact with individual virtual patients.
    trial       Interact with trials.

See `isct help <command>` for more information on a specific command.
"""

from docopt import docopt
import importlib
import logging
import logging.handlers
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
    args = docopt(__doc__, version="isct 0.0.1", options_first=True, argv=argv)

    # ensure the path for the log file (`--log`) is an existing directory
    s = schema.Schema({
        '--log':
        schema.And(schema.Use(str),
                   lambda p: os.path.isdir(pathlib.Path(p).parent) is True,
                   error='Invalid path for logfile.'),
        str:
        object,
    })
    try:
        args = s.validate(args)
    except schema.SchemaError as e:
        logging.critical(e)
        exit(__doc__)

    # Setup a rotating file handler at the indicated log file location. The
    # logfile is given a maximum size of ~1MB before it rotates.
    fh = logging.handlers.RotatingFileHandler(args['--log'],
                                              maxBytes=1000000,
                                              backupCount=5)
    fh.setFormatter(
        logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(fh)

    # store the invoked, validated arguments
    logging.debug(f'Invoked `isct` with args: {args}')

    # supported commands
    valid_commands = ['trial', 'patient', 'container']

    # extract command and arguments
    cmd = args['<command>']
    arg = args['<args>']

    # command is valid: call the `cmd` module with arguments `cmd + arg`
    if cmd in valid_commands:
        return load_module(cmd)([cmd] + arg)

    # format for error message
    err_msg = "The command `{}...` is not an isct command. See `isct help`."

    # command is neither a valid command nor `help`: exit
    if cmd not in ['help']:
        logging.critical(err_msg.format(cmd))
        sys.exit()

    # help requested with any specific command / argument
    if len(arg) == 0 or arg[0] in ['help']:
        sys.exit(__doc__)

    # help requested with a specific valid command: show help of that command
    if arg[0] in valid_commands:
        return load_module(arg[0])(['-h'])

    # requested help with invalid command
    logging.critical(err_msg.format(arg[0]))
    sys.exit()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
