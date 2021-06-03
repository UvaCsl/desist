"""Command-line utility for the eventhandling.

This provides a basic ``click``-based command-line utility that uses a
concrete API of the abstract ``desist.eventhander.api.API`` implementation.
The utility attaches the ``event``, ``example``, and ``test`` commands.
"""
import click

from .api import API


@click.command()
@click.pass_context
def event(ctx):
    """Invokes the ``API.event`` call to dispatch the event evaluation."""
    ctx.obj.event()


@click.command()
@click.pass_context
def example(ctx):
    """Invokes the ``API.example`` call to dispatch the example evaluation."""
    ctx.obj.example()


@click.command()
@click.pass_context
def test(ctx):
    """Invokes the ``API.test`` call to dispatch the test evaluation."""
    ctx.obj.test()


def event_handler(api_class=API):
    """Initialise the event handler API.

    Initialises the click-based command-line utility where the API is defined
    by the passed class or function. The argument supports any function that
    accepts a patient path and event id, and returns an initialised API
    instance.

    This results in commands formatted as, with ``$id`` the desired event ID:

    >>> python3 API.py /patient/ $id event
    """

    @click.group()
    @click.argument('patient', type=click.Path(exists=True))
    @click.argument('event', type=int)
    @click.pass_context
    def cli(ctx, patient, event):
        ctx.obj = api_class(patient, event)

    # attach the default commands
    for command in [event, example, test]:
        cli.add_command(command)

    return cli
