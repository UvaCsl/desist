import click

from .api import API


@click.command()
@click.pass_context
def event(ctx):
    ctx.obj.event()


@click.command()
@click.pass_context
def example(ctx):
    ctx.obj.example()


@click.command()
@click.pass_context
def test(ctx):
    ctx.obj.test()


def event_handler(api_class=API):
    """Initialise the event handler API.

    Initialises the click-based command-line utility where the API is defined
    by the passed class or function. The argument suppors any function that
    accepts a patient path and event id, and returns an initialised API
    instance.
    """

    @click.group()
    @click.argument('patient', type=click.Path(exists=True))
    @click.argument('event', type=int)
    @click.pass_context
    def cli(ctx, patient, event):
        ctx.obj = api_class(patient, event)
        ctx.obj.event()

    # attach the default commands
    for command in [event, example, test]:
        cli.add_command(command)

    return cli
