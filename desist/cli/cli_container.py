"""The subcommand for the command-line interface regarding containers."""
import click

from desist.isct.container import create_container
from desist.isct.runner import new_runner


@click.group()
def container():
    """The container subcommand.

    The `container` command interacts with containerised virtual environment,
    such as Docker and Singularity containers. This provides an uniform
    interface for creating either Docker or Singularity containers from the
    same directories, as long as the corresponding `Dockerfile` or
    `Singularity.def` definition files are present to define the environments.
    """


@container.command()
@click.argument('path', type=click.Path(exists=True), nargs=-1)
@click.option('-s', '--singularity', type=click.Path(exists=True))
@click.option('-x', '--dry', is_flag=True, default=False)
def create(path, singularity, dry):
    """Create Docker or Singularity containers.

    The container is created from the directory located at `PATH`. This
    directory should contain the corresponding definition files for either
    Docker or Singularity.
    """
    for p in path:
        container = create_container(p,
                                     container_path=singularity,
                                     runner=new_runner(dry))
        container.create()


@container.command()
@click.argument('container', type=str)
@click.argument('id', type=int)
@click.argument('patient', type=click.Path(exists=True), nargs=-1)
@click.option('-s', '--singularity', type=click.Path(exists=True))
@click.option('-x', '--dry', is_flag=True, default=False)
def run(container, id, patient, singularity, dry):
    """Run Docker or Singularity containers.

    This runs the patient simulation using the specified Docker or Singularity
    container. The patient is located at PATIENT path and the event
    corresponding to the event's ID is evaluated.
    """
    for p in patient:
        container = create_container(p,
                                     container_path=singularity,
                                     runner=new_runner(dry))

        container.run()
