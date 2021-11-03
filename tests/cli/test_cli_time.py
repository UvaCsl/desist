import pathlib
from click.testing import CliRunner

from desist.cli.time import time
from tests.isct.test_utilities import timing_test_log


def test_cli_time(tmpdir):
    logfile = pathlib.Path(tmpdir).joinpath('logfile')
    logfile.write_text(timing_test_log)
    expected_line_count = len(timing_test_log.splitlines())

    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(time, str(logfile))
        assert result.exit_code == 0
        assert len(result.output.splitlines()) == expected_line_count
