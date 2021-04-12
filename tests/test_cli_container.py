import pathlib

from click.testing import CliRunner
from desist.cli.cli_container import create, run


# FIXME: make these parametric over `[Docker, Singularity]`

def test_container_create(tmpdir):
    runner = CliRunner()
    path = pathlib.Path(tmpdir)
    with runner.isolated_filesystem():
        result = runner.invoke(create, [str(path), '-x'])
        assert result.exit_code == 0
        for k in ['docker', 'build', '-t', str(path)]:
            assert k in result.output


def test_container_create_multiple(tmpdir):
    runner = CliRunner()
    path = pathlib.Path(tmpdir)
    with runner.isolated_filesystem():
        result = runner.invoke(create, [str(path), str(path), '-x'])
        assert result.exit_code == 0
        assert result.output.count(str(path)) == 2


def test_container_run(tmpdir):
    runner = CliRunner()
    path = pathlib.Path(tmpdir)
    with runner.isolated_filesystem():
        result = runner.invoke(run, ['container', '0', str(path), '-x'])
        assert result.exit_code == 0
        for k in ['docker', 'run', 'container']:
            assert k in result.output
