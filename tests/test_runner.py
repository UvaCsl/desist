import pytest

from isct.runner import Runner, LocalRunner, Logger, ParallelRunner
from isct.runner import new_runner


class DummyRunner(Runner):
    def __init__(self):
        super().__init__()
        self.output = []

    def __contains__(self, string):
        return any([string in output for output in self.output])

    def run(self, cmd, check=True):
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
    cmd = 'isct trial this is a dummy command'
    runner = ParallelRunner()
    runner.run(cmd.split())

    # ensure the `cmd` is echoed into `stdout`
    out, _ = capsys.readouterr()
    assert cmd in out
