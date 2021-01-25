import click
import logging
import pathlib
from logging.handlers import RotatingFileHandler

from .cli_container import container
from .cli_patient import patient
from .cli_trial import trial

# default path for logs
logfile = pathlib.Path('/tmp/isct.log')
logger = logging.getLogger(__name__)


@click.group()
@click.option('-v', '--verbose', is_flag=True, default=False)
def cli(verbose):
    """des-ist."""

    # FIXME: add `click.argument` to dictate the log file location

    # Setup the basic logger with a rotating logger to rotate the logfiles
    # every 100kB, cycling through 10 backups.
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
        handlers=[
            # The logfiles rotate every 100kB.
            RotatingFileHandler(str(logfile), maxBytes=10000, backupCount=10)
        ],
    )

    if verbose:
        # define stream handler to log to console
        logger = logging.getLogger()
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        logger.addHandler(ch)


cli.add_command(container)
cli.add_command(patient)
cli.add_command(trial)
