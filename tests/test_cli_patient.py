from click.testing import CliRunner
import pathlib
import pytest

from isct.cli_patient import run
from isct.cli_trial import create
from isct.events import default_events


# FIXME: generic over `[Docker, Singularity]`


def test_patient_run(tmpdir):
    runner = CliRunner()
    path = pathlib.Path(tmpdir)
    with runner.isolated_filesystem():
        result = runner.invoke(create, [str(path)])
        assert result.exit_code == 0

        patient = path.joinpath('patient_00000')
        result = runner.invoke(run, [str(patient)])
        assert result.exit_code == 0
        for k in ['docker', 'run', '-v', ':/patient']:
            assert k in result.output
        assert all([m in result.output for m in default_events.models])
