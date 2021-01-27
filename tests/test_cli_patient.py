from click.testing import CliRunner
import os
import pathlib
import pytest

from isct.cli_patient import run
from isct.cli_trial import create
from isct.utilities import OS
from isct.events import default_events
from isct.patient import patient_config


@pytest.mark.parametrize('platform', [OS.MACOS, OS.LINUX])
def test_patient_run(mocker, tmpdir, platform):
    mocker.patch('isct.utilities.OS.from_platform', return_value=platform)

    runner = CliRunner()
    path = pathlib.Path('test')
    with runner.isolated_filesystem():
        result = runner.invoke(create, [str(path), '-x'])
        assert result.exit_code == 0

        patient = path.joinpath(f'patient_00000/{patient_config}')
        result = runner.invoke(run, [str(patient), '-x'])
        assert result.exit_code == 0

        for k in ['docker', 'run', '-v', ':/patient']:
            assert k in result.output
        assert all([m in result.output for m in default_events.models])


@pytest.mark.parametrize('platform', [OS.MACOS, OS.LINUX])
def test_patient_run_singularity(mocker, tmpdir, platform):
    mocker.patch('isct.utilities.OS.from_platform', return_value=platform)

    runner = CliRunner()
    path = pathlib.Path('test')
    singularity = pathlib.Path('singularity')
    with runner.isolated_filesystem():
        os.makedirs(singularity)
        result = runner.invoke(
            create,
            [str(path), '-x', '-s', str(singularity)])
        assert result.exit_code == 0

        patient = path.joinpath(f'patient_00000/{patient_config}')
        result = runner.invoke(run, [str(patient), '-x'])
        assert result.exit_code == 0

        for k in ['singularity', 'run', '-B', ':/patient']:
            assert k in result.output
        assert all([m in result.output for m in default_events.models])

        # if the singularity directory is not present, the running should fail
        os.rmdir(singularity)
        result = runner.invoke(run, [str(patient), '-x'])
        assert result.exit_code == 2
        assert f'`{str(singularity.absolute())}` not present' in result.output
