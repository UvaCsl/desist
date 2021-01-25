import click
from .cli_container import container
from .cli_patient import patient
from .cli_trial import trial


@click.group()
def cli():
    """des-ist."""

    # TODO:
    # - setup rotating log files
    # - setup verbosity of global logging behaviour


cli.add_command(container)
cli.add_command(patient)
cli.add_command(trial)
