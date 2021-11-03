"""The main entry point for the command-line interface."""

import click
import logging
from logging.handlers import RotatingFileHandler

from .container import container
from .patient import patient
from .trial import trial
from .time import time


@click.group()
@click.option('-v',
              '--verbose',
              is_flag=True,
              default=False,
              help="Increase verbosity: shows all `DEBUG` logs.")
@click.option('--log',
              type=click.Path(writable=True),
              help="Path where log files are written to.")
def cli(verbose, log):
    """des-ist.

    Discrete Event Simulation for In Silico computational Trials.

    This command-line utility supports evaluation of in silico simulation
    of virtual patient cohorts. The utility provides commands to create,
    run, and analyse in silico trials.
    """
    # initialise the logging on `DEBUG` level without any handlers
    logging.basicConfig(level=logging.DEBUG, handlers=[])

    # add a streaming log to console
    ch = logging.StreamHandler()
    level = logging.DEBUG if verbose else logging.WARNING
    ch.setLevel(level)
    logging.getLogger().addHandler(ch)

    # if a logfile is provided, write _all_ messages to the files
    if log:
        rfh = RotatingFileHandler(log, maxBytes=100000, backupCount=5)
        rfh.setLevel(logging.DEBUG)
        fmt_str = '%(asctime)s | %(name)s | %(levelname)s | %(message)s'
        rfh.setFormatter(logging.Formatter(fmt_str))
        logging.getLogger().addHandler(rfh)


cli.add_command(container)
cli.add_command(patient)
cli.add_command(trial)
cli.add_command(time)
