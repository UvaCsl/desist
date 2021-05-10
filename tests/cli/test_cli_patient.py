from click.testing import CliRunner
import os
import pathlib
import pytest

from desist.cli.patient import run, reset
from desist.cli.trial import create
from desist.isct.utilities import OS, MAX_FILE_SIZE
from desist.isct.events import default_events
from desist.isct.trial import Trial, trial_config


@pytest.mark.parametrize('platform', [OS.MACOS, OS.LINUX])
def test_patient_run(mocker, tmpdir, platform):
    mocker.patch('desist.isct.utilities.OS.from_platform', return_value=platform)

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
    mocker.patch('desist.isct.utilities.OS.from_platform', return_value=platform)

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
    mocker.patch('desist.isct.utilities.OS.from_platform', return_value=platform)

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


@pytest.mark.parametrize('platform', [OS.MACOS, OS.LINUX])
def test_patient_run_container_path(mocker, tmpdir, platform):
    mocker.patch('desist.isct.utilities.OS.from_platform',
                 return_value=platform)

    runner = CliRunner()
    path = pathlib.Path('test')

    local = pathlib.Path('local')
    remote = pathlib.Path('remote')

    with runner.isolated_filesystem():
        os.makedirs(local)
        os.makedirs(remote)

        result = runner.invoke(
            create,
            [str(path), '-x', '-s', str(local)])
        assert result.exit_code == 0

        trial = Trial.read(path.joinpath(trial_config))
        patient = list(trial)[0]

        # runs fine: local container directory is present
        result = runner.invoke(run, [str(patient.dir), '-x'])
        assert result.exit_code == 0

        # should fail: local container directory not present
        os.rmdir(local)
        result = runner.invoke(run, [str(patient.dir), '-x'])
        assert result.exit_code == 2

        # should run fine: override the container directory manually
        result = runner.invoke(run,
                               [str(patient.dir), '-x', '-c', str(remote)])
        assert result.exit_code == 0


@pytest.mark.parametrize('platform', [OS.MACOS, OS.LINUX])
def test_patient_reset(mocker, tmpdir, platform):
    mocker.patch('desist.isct.utilities.OS.from_platform', return_value=platform)

    runner = CliRunner()
    path = pathlib.Path('test')
    with runner.isolated_filesystem():
        result = runner.invoke(create, [str(path), '-x'])
        assert result.exit_code == 0
        trial = Trial.read(path.joinpath(trial_config))

        # artificially set patients to completed
        for p in trial:
            p.completed = True
            p.write()
        assert all([p.completed for p in trial])

        result = runner.invoke(reset, [str(p.dir) for p in trial])
        assert result.exit_code == 0
        assert all([p.completed for p in trial]) is False

        # remove file and directories
        pdir = [p.dir for p in trial][0]
        test_file = pathlib.Path(pdir).joinpath('test')
        test_file.touch()
        assert os.path.isfile(test_file)

        result = runner.invoke(reset, [str(pdir), '-r', 'test'])
        assert result.exit_code == 0
        assert not os.path.isfile(test_file)
