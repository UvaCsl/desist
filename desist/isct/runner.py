"""Command runners.

The :class:`~isct.runner.Runner` is responsible for evaluating commands. By
providing differents implementations for :meth:`~isct.runner.Runner.run` the
behaviour can be changed to, for example, logging commands, running commands
sequentially, to emitting instructions for parallel evaluation.
"""
import abc
import click
import subprocess
import logging
import os
import sys


def new_runner(verbose: bool, parallel: bool = False, qcg: bool = False):
    """Return an initialised runner matching `verbose` and parallel`.

    Note: when ambiguous arguments are provided, the function only returns the
    :class:~`isct.Logger` and does not perform any error checking. This is
    assumed to be handled already by the caller.

    Args:
        verbose: If the evaluation should only be verbose to console.
        parallel: If the evaluation should happen in ``GNU Parallel``.
        qcg: If the evaluation should happen using ``QCG``
    """
    if verbose or (parallel and qcg):
        return Logger()

    if parallel:
        return ParallelRunner()

    if qcg:
        return QCGRunner()

    return LocalRunner()


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
    def run(self, cmd, check: bool = True, shell: bool = False):
        """Run the provided command.

        Implements how the command should be evaluated.

        Args:
            cmd: The command to be evaluated, either as a list of strings, or
                 as a space-separated string of commands.
            check: If successfull evaluation of the command is enforced.
            shell: If `shell=True` is passed to `subprocess`.
        """

        # FIXME: `shell = False` is not needed in all commands

    def wait(self):
        """A routine to wait until the runner is done.

        For synchronous runners this routine is superfluous, as all simulations
        will be done once the run finalises. However, for asynchronous runners,
        such as :class:~`isct.runner.QCGRunner`, ``wait`` will ensure all jobs
        are completed before continuing.
        """
        pass


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

    The commands are evaluated using ``subprocess.run``. The commands and its
    output are echoed into the log files and/or the console by providing the
    command-line arguments ``--log LOGFILE`` or ``-v``.

    >>> isct --log /tmp/isct.log trial run /path/to/trial/
    >>> isct -v trial run /path/to/trial/
    """
    def __init__(self):
        super().__init__()
        self.write_config = True

    def run(self, cmd, check: bool = True, shell: bool = False):
        """Run commands locally by invoking ``subprocess.run``.

        The preferred approach is to provide the commands as a list of strings
        that can be passed into ``subprocess.run`` directly, without having
        to invoke ``shell=True``. If there is no other way to evaluate the
        command on the local system, the optional boolean can be set.

        Args:
            cmd: The command to be evaluated.
            check: Successfull outcome of the command ``cmd`` is asserted. On
                   failure an message is displayed.
            shell: If ``shell``: ``shell=True`` is passed into
                   ``subprocess.run``. However, it is adviced to not run the
                   commands with ``shell=True`` explicitly if it can be
                   avoided.
        """
        msg = self.format(cmd)
        logging.info(msg)

        try:
            process = subprocess.run(cmd,
                                     check=check,
                                     shell=shell,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT,
                                     env={**os.environ})

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
    """The parallel runner emits the commands over `stdout`.

    It is assumed that :class:`isct.runner.ParallelRunner` is combined with
    ``GNU Parallel``. Thus, the required commands are emitted over ``stdout``
    to be picked up and distributed by ``parallel``, for example

    >>> isct trial run mr-clean --parallel | parallel
    """
    def __init__(self):
        super().__init__()

    def run(self, cmd):
        """Emit commands over ``stdout`` for ``GNU Parallel``."""
        msg = self.format(cmd)
        logging.info(msg)
        sys.stdout.write(f'{msg}\n')


class QCGRunner(Runner):
    """Run simulation jobs through ``QCG PilotJob``.

    The :class:`isct.runner.QCGRunner` requires ``QCG Pilot-Job`` to be present
    on the system and uses its manager to run the required jobs. This class
    keeps track of a ``LocalManager`` and a corresponding ``Jobs`` instance.
    The latter instance is used to keep track of the required jobs to be
    evaluated, where each command passed to ``run`` is appended to the job
    list.

    Note: the ``LocalManager`` is only initialised on
    :func:`isct.runner.QCGrunner.wait` and not immediately when the class is
    initialised. Only when commands are to be evaluated, we really need the
    manager to be active, until then we delay the QCG service.

    Afterwards, :func:`isct.runner.QCGRunner.wait` is invoked, which submits
    all jobs present in ``self.jobs`` to the queue and waits for their
    completion. The ``LocalManager`` is given full control to schedule the
    jobs across the available resources, which can either be local, cloud, or
    HPC-based environments. Note, that when running on multiple machines, the
    Python environment including `qcg-pilotmanager` should be accessible, as no
    specific ``venv`` settings are provided here.
    """
    def __init__(self):
        from qcg.pilotjob.api.job import Jobs
        from qcg.pilotjob.api.manager import LocalManager as QCGManager
        super().__init__()
        self.jobs = Jobs()
        self.manager = QCGManager

    def run(self, cmd):
        """Add the command to the ``QCG`` job queue."""
        self.jobs.add(script=' '.join(cmd), numCores=1)

    def wait(self):
        """Submit all jobs and wait until ``QCG`` has completed all jobs.

        Note: the jobs are evaluated on all available resources detected by the
        ``qcg.pilotjob.api.manager.LocalManager``.
        """
        manager = self.manager()
        manager.submit(self.jobs)
        manager.wait4all()
        manager.finish()
