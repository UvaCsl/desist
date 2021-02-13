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
    """Abstract implementation of a command runner.

    The `Runner` classes are in charge of evaluating the provided commands and
    many variations can be imagined, ranging from locally running the commands,
    to merely logging the commands to the console.

    The `write_config` attribute determines if the runner allows that a patient
    configuration is updated and the updates written to disk. For scenarios
    where the commands are only logged, i.e. the are not evaluated, the config
    files should probably not be updated. This behaviour is controlled by
    setting the `write_config` attribute in child implementations.
    """
    def __init__(self):
        self.write_config = False

    def format(self, cmd):
        """Formatting for the command for logging."""
        if isinstance(cmd, list):
            return ' '.join(cmd)
        return cmd

    @abc.abstractmethod
    def run(self, cmd, check=True, shell=False):
        """Run command. Report on result if check == True"""


class Logger(Runner):
    """A runner implementation printing the commands to `stdout`."""
    def __init__(self):
        super().__init__()

    def run(self, cmd, check=True, shell=False):
        """Prints the commands to `stdout`."""
        msg = self.format(cmd)
        logging.info(msg)
        click.echo(msg)


class LocalRunner(Runner):
    """A runner evaluating commands on the local machine.

    The commands and its output are echoed into the logs, which can be enabled
    by passing `-v` argument to the main command.
    """
    def __init__(self):
        super().__init__()
        self.write_config = True

    def run(self, cmd, check=True, shell=False):
        """Prints the commands to `stdout`."""
        msg = self.format(cmd)
        logging.info(msg)

        try:
            process = subprocess.run(cmd,
                                     check=check,
                                     shell=shell,
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
        msg = self.format(cmd)
        logging.info(msg)
        sys.stdout.write(f'{msg}\n')
