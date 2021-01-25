import logging
import pathlib
import pytest

from click.testing import CliRunner
from isct.cli import cli


def test_isct_cli():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli)
        assert result.exit_code == 0


def test_isct_cli_logger():
    runner = CliRunner()
    with runner.isolated_filesystem():
        cmd = ['trial', 'create', '--help']
        result = runner.invoke(cli, cmd)
        assert result.exit_code == 0

        # obtain the default logger count
        logger = logging.getLogger()
        count = len(logger.handlers)

        # making the runner verbose, add one additional logger
        cmd = ['-v'] + cmd
        result = runner.invoke(cli, cmd)
        assert result.exit_code == 0
        assert len(logger.handlers) == count + 1


def test_isct_cli_log_location():
    runner = CliRunner()
    with runner.isolated_filesystem():
        path = pathlib.Path('tmp.log')
        assert not path.exists()
        cmd = ['--log', str(path), 'trial', 'create', '--help']
        result = runner.invoke(cli, cmd)
        assert result.exit_code == 0
        assert path.exists()
