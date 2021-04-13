import os

from click.testing import CliRunner
from desist.cli.cli import cli


def test_isct_cli():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli)
        assert result.exit_code == 0


def test_isct_cli_logfile():
    runner = CliRunner()
    with runner.isolated_filesystem():
        cmd = ['--log', 'file.log', 'trial', 'create', '--help']
        result = runner.invoke(cli, cmd)
        assert result.exit_code == 0
        assert os.path.isfile('file.log')
