from click.testing import CliRunner
import pathlib
import pytest

from isct.cli_patient import run
from isct.cli_trial import create
from isct.utilities import OS
from isct.events import default_events
from isct.patient import patient_config


# FIXME: generic over `[Docker, Singularity]`


@pytest.mark.parametrize('platform', [OS.MACOS, OS.LINUX])
def test_patient_run(mocker, tmpdir, platform):
    mocker.patch('isct.utilities.OS.from_platform', return_value=platform)

    runner = CliRunner()
    path = pathlib.Path(tmpdir).joinpath('test')
    with runner.isolated_filesystem():
        result = runner.invoke(create, [str(path), '-x'])
        assert result.exit_code == 0

        patient = path.joinpath(f'patient_00000/{patient_config}')
        result = runner.invoke(run, [str(patient), '-x'])
        assert result.exit_code == 0

        for k in ['docker', 'run', '-v', ':/patient']:
            assert k in result.output
        assert all([m in result.output for m in default_events.models])
