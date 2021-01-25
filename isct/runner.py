import abc
import click
import subprocess
import logging
import sys


def new_runner(verbose, parallel=False):
    if verbose:
        runner = Logger()
    else:
        runner = ParallelRunner() if parallel else LocalRunner()
    return runner


class Runner(abc.ABC):
    def __init__(self):
        pass

    @abc.abstractmethod
    def run(self, cmd, check=True):
        """Run command. Report on result if check == True"""


class Logger(Runner):
    """A runner implementation printing the commands to `stdout`."""
    def __init__(self):
        super().__init__()

    def run(self, cmd, check=True):
        """Prints the commands to `stdout`."""
        msg = ' '.join(cmd)
        logging.info(msg)
        click.echo(msg)


class LocalRunner(Runner):
    """A runner evaluating commands on the local machine.

    The commands and its output are echoed into the logs, which can be enabled
    by passing `-v` argument to the main command.
    """
    def __init__(self):
        super().__init__()

    def run(self, cmd, check=True):
        """Prints the commands to `stdout`."""
        msg = ' '.join(cmd)
        logging.info(msg)

        try:
            process = subprocess.run(cmd,
                                     check=check,
                                     shell=False,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT)

        except subprocess.CalledProcessError as e:
            msg = f'Command: `{msg}` failed with error: `{e}`.'
            logging.critical(f'Subprocess failed: {e}.')
            logging.critical(f'Captured output: {e.stdout.decode().rstrip()}')

            # report to console
            click.echo(click.style(msg, fg="red"))

            if check:
                return False

        # capture the output of the subcommand in the logs
        for line in process.stdout.decode().split('\n'):
            logging.info(line)

        return True


class ParallelRunner(Runner):
    def __init__(self):
        super().__init__()

    def run(self, cmd):
        msg = ' '.join(cmd)
        logging.info(msg)
        sys.stdout.write(f'{msg}\n')
