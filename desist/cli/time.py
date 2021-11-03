"""The subcommand for to extract start and elapsed simulation times."""
import click

from desist.isct.utilities import extract_simulation_times


@click.command()
@click.argument('logfile', nargs=-1,
                type=click.Path(exists=True, allow_dash=True))
def time(logfile):
    """Extract the start and elapsed time for each model in the log file.

    For each logfile the starting times are reported together with the elapsed
    time between consecutive model invocations.
    """
    for log in logfile:
        click.echo(extract_simulation_times(log))
