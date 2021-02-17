from click.testing import CliRunner
import os
import pathlib
import pytest

from isct.cli_patient import run
from isct.cli_trial import create
from isct.utilities import OS, MAX_FILE_SIZE
from isct.events import default_events
from isct.trial import Trial, trial_config
from isct.patient import patient_config


@pytest.mark.parametrize('platform', [OS.MACOS, OS.LINUX])
def test_patient_run(mocker, tmpdir, platform):
    mocker.patch('isct.utilities.OS.from_platform', return_value=platform)

    runner = CliRunner()
    path = pathlib.Path('test')
    with runner.isolated_filesystem():
        result = runner.invoke(create, [str(path), '-x'])
        assert result.exit_code == 0

        trial = Trial.read(path.joinpath(trial_config))
        patient = list(trial)[0]

        result = runner.invoke(run, [str(patient.dir), '-x'])
        assert result.exit_code == 0

        for k in ['docker', 'run', '-v', ':/patient']:
            assert k in result.output

        # FIXME: this tag conversion should be improved
        tags = [event.replace("_", "-") for event in default_events.models]
        assert all([m in result.output for m in tags])


@pytest.mark.parametrize('platform', [OS.MACOS, OS.LINUX])
def test_patient_keep_files(mocker, tmpdir, platform):
    mocker.patch('isct.utilities.OS.from_platform', return_value=platform)

    runner = CliRunner()
    path = pathlib.Path('test')
    with runner.isolated_filesystem():
        result = runner.invoke(create, [str(path), '-x'])
        assert result.exit_code == 0

        trial = Trial.read(path.joinpath(trial_config))
        patient = list(trial)[0]
        large_file = patient.dir.joinpath('large-file')

        # create a large file
        with open(large_file, 'wb') as outfile:
            outfile.seek(MAX_FILE_SIZE + 10)
            outfile.write(b"\0")

        assert large_file.exists()

        result = runner.invoke(run, [str(patient.dir), '-x'])
        result = runner.invoke(run, [str(patient.dir), '-x', '--keep-files'])
        assert result.exit_code == 0
        assert large_file.exists(), "no large files should be removed"

        result = runner.invoke(run, [str(patient.dir), '-x', '--clean-files'])
        assert result.exit_code == 0
        assert not large_file.exists(), "all large files should be removed"


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

        trial = Trial.read(path.joinpath(trial_config))
        patient = list(trial)[0]

        result = runner.invoke(run, [str(patient.dir), '-x'])
        assert result.exit_code == 0

        for k in ['singularity', 'run', '-B', ':/patient']:
            assert k in result.output

        # FIXME: this tag conversion should be improved
        tags = [event.replace("_", "-") for event in default_events.models]
        assert all([m in result.output for m in tags])

        # if the singularity directory is not present, the running should fail
        os.rmdir(singularity)
        result = runner.invoke(run, [str(patient.dir), '-x'])
        assert result.exit_code == 2
        assert f'`{str(singularity.absolute())}` not present' in result.output
