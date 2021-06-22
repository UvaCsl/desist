import pytest

from desist.isct.runner import Runner, LocalRunner, Logger, ParallelRunner
from desist.isct.runner import QCGRunner
from desist.isct.runner import new_runner


class DummyRunner(Runner):
    """A dummy implementation of the runner capturing all outputs.

    All outputs that would normally be evaluated as commands are captured in
    the `self.output` attribute. This enables testing if the right commands are
    emitted by the classes. The `__contains__` routine is implemented to easily
    test if commands were emitted.

    >>> runner = DummyRunner()
    >>> ...
    >>> assert 'some specific command' in runner, 'command not emitted'

    """
    def __init__(self, write_config=False):
        super().__init__()
        self.output = []
        self.write_config = write_config

    def __str__(self):
        """String representation of stored commands, one per line."""
        return '\n'.join([' '.join(string) for string in self.output])

    def __contains__(self, string):
        """Test if the string is contained in any of the captured commands."""
        return any([string in ' '.join(output) for output in self.output])

    def clear(self):
        """Clears the stored commands in `self.output`."""
        self.output = []

    def run(self, cmd, check=True, shell=False):
        """Mocks the command by appending the command to `self.output`."""
        self.output.append(cmd)
        return cmd


@pytest.mark.parametrize('verbose, parallel, logger', [
    (False, False, LocalRunner),
    (True, False, Logger),
    (False, True, ParallelRunner),
    (True, True, Logger),
])
def test_new_runner(verbose, parallel, logger):
    assert isinstance(new_runner(verbose, parallel), logger)


@pytest.mark.parametrize('verbose, parallel, qcg, logger', [
    (False, False, True, QCGRunner),
    (False, True, True, Logger),
    (True, True, True, Logger),
])
def test_new_runner_qcg(verbose, parallel, qcg, logger):
    pytest.importorskip("qcg.pilotjob.api.manager")
    assert isinstance(new_runner(verbose, parallel, qcg), logger)


def test_test_runner():
    runner = DummyRunner()
    cmd = ["cmd", "cmd"]
    assert runner.run(cmd) == cmd
    assert all(c in runner for c in cmd)


def test_local_runner():
    runner = LocalRunner()
    assert runner.run("true")
    assert not runner.run("false")
    assert runner.run("false", check=False)


def test_parallel_runner(capsys):
    cmd = 'desist trial this is a dummy command'
    runner = ParallelRunner()
    runner.run(cmd.split())

    # ensure the `cmd` is echoed into `stdout`
    out, _ = capsys.readouterr()
    assert cmd in out


def test_qcg_runner():
    pytest.importorskip("qcg.pilotjob.api.manager")

    cmd = 'true'
    runner = QCGRunner()
    assert len(runner.jobs.jobs()) == 0
    runner.run(cmd.split())
    assert len(runner.jobs.jobs()) == 1

    # the command should be present with exactly a single core allocated
    job = runner.jobs.jobs()[0]
    assert job['execution']['script'] == cmd
    assert job['resources']['numCores']['exact'] == 1

    runner.wait()
