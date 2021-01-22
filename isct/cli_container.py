import click

from .container import create_container
from .runner import create_runner


@click.group()
def container():
    """Container"""


@container.command()
@click.argument('path', type=click.Path(exists=True), nargs=-1)
@click.option('-s', '--singularity', type=click.Path(exists=True))
@click.option('-x', '--dry', is_flag=True, default=False)
def create(path, singularity, dry):
    """Create Docker/Singularity container from PATH."""

    for p in path:
        container = create_container(p, runner=create_runner(dry))
        container.create()


@container.command()
@click.argument('container', type=str)
@click.argument('id', type=int)
@click.argument('patient', type=click.Path(exists=True), nargs=-1)
@click.option('-x', '--dry', is_flag=True, default=False)
def run(container, id, patient, dry):
    """Run containers."""

    # TODO:
    # - create container instance
    # - verify container present

    for p in patient:
        container = create_container(p, runner=create_runner(dry))
        container.run()

        # - create patient instance
        # - run patient inside container with ID
