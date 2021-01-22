from isct.runner import Runner, LocalRunner, Logger, create_runner


class DummyRunner(Runner):
    def __init__(self):
        super().__init__()
        self.output = []

    def __contains__(self, string):
        return any([string in output for output in self.output])

    def run(self, cmd, check=True):
        self.output.append(cmd)
        return cmd


def test_create_runner():
    assert isinstance(create_runner(True), Logger)
    assert isinstance(create_runner(False), LocalRunner)


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
