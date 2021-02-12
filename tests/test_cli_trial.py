from click.testing import CliRunner
import pathlib
import pytest
import os

from isct.cli_trial import create, append, run, list_key
from isct.trial import Trial, trial_config
from isct.utilities import OS

# FIXME: `dry` run does still create all directories though...


@pytest.mark.parametrize('n', [1, 5])
def test_trial_create(n):
    runner = CliRunner()
    path = pathlib.Path('test')
    with runner.isolated_filesystem():
        result = runner.invoke(create, [str(path), '-n', n, '-x'])
        assert result.exit_code == 0
        assert len(list(filter(lambda p: p.is_dir(), path.iterdir()))) == n

        trial = Trial.read(path.joinpath(trial_config))
        assert trial.get('sample_size') == n
        assert f'{os.path.basename(trial.dir)}:/trial' in result.output
        assert 'container-path' in trial
        assert trial['container-path'] is None

        for patient in trial.patients:
            assert f'trial/{patient}' in result.output


@pytest.mark.parametrize('n', [1, 5])
def test_trial_create_singularity(n):
    runner = CliRunner()
    path = pathlib.Path('test')
    singularity = pathlib.Path('singularity')
    with runner.isolated_filesystem():
        result = runner.invoke(
            create, [str(path), '-n', n, '-x', '-s',
                     str(singularity)])
        assert result.exit_code == 2

        os.makedirs(singularity)
        result = runner.invoke(
            create, [str(path), '-n', n, '-x', '-s',
                     str(singularity)])
        assert result.exit_code == 0

        trial = Trial.read(path.joinpath(trial_config))
        assert trial.get('sample_size') == n
        assert f'{os.path.basename(trial.dir)}:/trial' in result.output
        assert 'container-path' in trial
        assert trial['container-path'] == str(singularity.absolute())

        for patient in trial.patients:
            assert f'trial/{patient}' in result.output

        # modified container path in configuration, should fail on append
        trial['container-path'] = 'path/does/not/exist'
        trial.write()

        # appending should fail: missing container path
        result = runner.invoke(append, [str(path), '-x'])
        assert result.exit_code == 2
        assert '`path/does/not/exist` not present' in result.output

        # appending should fail: missing container path
        result = runner.invoke(run, [str(path), '-x'])
        assert result.exit_code == 2
        assert '`path/does/not/exist` not present' in result.output


def test_trial_overwrite():
    runner = CliRunner()
    path = pathlib.Path('test')
    with runner.isolated_filesystem():
        os.makedirs(path)
        result = runner.invoke(create, [str(path), '-x'])
        # should raise `UsageError`, not `sys.exit`
        assert result.exit_code == 2
        assert "already exists" in result.output


@pytest.mark.parametrize('n', [1, 5])
def test_trial_append(tmpdir, n):
    runner = CliRunner()
    path = pathlib.Path(tmpdir).joinpath('test')
    with runner.isolated_filesystem():
        result_c = runner.invoke(create, [str(path), '-n', n, '-x'])
        assert result_c.exit_code == 0
        result_a = runner.invoke(append, [str(path), '-n', n, '-x'])
        assert result_a.exit_code == 0
        assert len(list(filter(lambda p: p.is_dir(), path.iterdir()))) == 2 * n

        trial = Trial.read(path.joinpath(trial_config))
        assert trial.get('sample_size') == 2 * n

        # the first half should be in result of `create`
        # the other half should be in result of `append`
        for i, patient in enumerate(sorted(list(trial.patients))):
            if i < n:
                assert f'trial/{patient}' in result_c.output
            else:
                assert f'trial/{patient}' in result_a.output


@pytest.mark.parametrize('platform', [OS.MACOS, OS.LINUX])
@pytest.mark.parametrize('parallel', [True, False])
@pytest.mark.parametrize('num_patients', [1, 2, 5])
def test_trial_run(mocker, tmpdir, platform, num_patients, parallel):
    mocker.patch('isct.utilities.OS.from_platform', return_value=platform)

    runner = CliRunner()
    path = pathlib.Path(tmpdir).joinpath('test')
    with runner.isolated_filesystem():
        result = runner.invoke(create, [str(path), '-n', num_patients, '-x'])
        assert result.exit_code == 0

        cmd = [str(path)]
        cmd = cmd + ['--parallel'] if parallel else cmd + ['-x']
        result = runner.invoke(run, cmd)
        assert result.exit_code == 0

        for i in range(num_patients):
            assert f'patient_{i:05}' in result.output

        if parallel:
            assert 'docker' not in result.output
        else:
            for k in ['docker', 'run']:
                assert k in result.output


@pytest.mark.parametrize('num_patients', [1, 2, 5])
def test_trial_list(tmpdir, num_patients):
    runner = CliRunner()
    path = pathlib.Path(tmpdir).joinpath('test')

    with runner.isolated_filesystem():
        result = runner.invoke(create, [str(path), '-n', num_patients, '-x'])
        assert result.exit_code == 0

        # prefix is uniform: should be counted equal to number of patients
        result = runner.invoke(list_key, [str(path), 'prefix'])
        assert result.exit_code == 0
        assert "'prefix'" in result.output
        assert f"'patient' ({num_patients})" in result.output

        # id is unique: should be counted only once per patient
        result = runner.invoke(list_key, [str(path), 'id'])
        assert result.exit_code == 0
        assert "'id'" in result.output
        for i in range(num_patients):
            assert f"'{i}' (1)" in result.output

        # when restricting the number of outputted entries, these are sorted
        # so this should only display the zero ID and not the others
        result = runner.invoke(list_key, [str(path), 'id', '-n', 1])
        assert result.exit_code == 0
        assert "'id'" in result.output
        assert "'0' (1)" in result.output
        for i in range(1, num_patients):
            assert f"'{i}' (1)" not in result.output
