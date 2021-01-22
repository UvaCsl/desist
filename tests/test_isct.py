from click.testing import CliRunner
from isct.isct import cli


def test_isct_cli():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli)
        assert result.exit_code == 0
