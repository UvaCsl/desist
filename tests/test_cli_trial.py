from click.testing import CliRunner
import pathlib
import pytest
import os

from isct.config import Config
from isct.cli_trial import create, append, run, list_key, outcome, archive
from isct.trial import Trial, trial_config
from isct.utilities import OS, MAX_FILE_SIZE

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
def test_trial_from_criteria_file(tmpdir, n):
    runner = CliRunner()
    path = pathlib.Path('test')
    with runner.isolated_filesystem():
        criteria = Config('{tmpdir}/criteria.yml', {
            'sample_size': n,
            'testkey': True
        })
        criteria.write()
        assert os.path.exists(criteria.path)

        result = runner.invoke(
            create,
            [str(path), '-c', str(criteria.path), '-x'])
        assert result.exit_code == 0
        assert len(list(filter(lambda p: p.is_dir(), path.iterdir()))) == n

        # ensure the config is passed to the virtual patient model
        assert '--config' in result.output

        # assert keys from criteria file end up in trial configurations
        trial = Trial.read(path.joinpath(trial_config))
        assert trial.get('sample_size') == n
        assert trial.get('testkey', False)


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


@pytest.mark.parametrize('keep_files', [True, False])
@pytest.mark.parametrize('platform', [OS.MACOS, OS.LINUX])
@pytest.mark.parametrize('parallel', [True, False])
@pytest.mark.parametrize('num', [1, 2, 5])
def test_trial_run(mocker, tmpdir, keep_files, platform, num, parallel):
    mocker.patch('isct.utilities.OS.from_platform', return_value=platform)

    keep_cmd = '--keep-files' if keep_files else '--clean-files'

    runner = CliRunner()
    path = pathlib.Path(tmpdir).joinpath('test')
    with runner.isolated_filesystem():
        result = runner.invoke(create, [str(path), '-n', num, '-x'])
        assert result.exit_code == 0

        cmd = [str(path)]
        cmd = cmd + ['--parallel'] if parallel else cmd + ['-x']
        cmd = cmd + [keep_cmd]

        # create a large file in one of the patients
        trial = Trial.read(path.joinpath(trial_config))
        large_file = list(trial)[0].dir.joinpath('large-file')
        with open(large_file, 'wb') as outfile:
            outfile.seek(MAX_FILE_SIZE + 10)
            outfile.write(b"\0")
        assert large_file.exists()

        result = runner.invoke(run, cmd)
        assert result.exit_code == 0

        for i in range(num):
            assert f'patient_{i:05}' in result.output

        if parallel:
            assert 'docker' not in result.output
            assert keep_cmd in result.output
        else:
            for k in ['docker', 'run']:
                assert k in result.output
            assert keep_files == large_file.exists()


@pytest.mark.parametrize('num_patients', [5])
def test_trial_outcome(tmpdir, num_patients):
    runner = CliRunner()
    path = pathlib.Path('test')
    with runner.isolated_filesystem():
        result = runner.invoke(create, [str(path), '-n', num_patients, '-x'])
        assert result.exit_code == 0

        trial = Trial.read(path.joinpath(trial_config))
        result = runner.invoke(outcome, [str(path), '-x'])
        assert result.exit_code == 0
        assert f'{trial.dir}:/trial' in result.output


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


@pytest.mark.parametrize('num_patients', [1, 2, 5])
def test_trial_archive(tmpdir, num_patients):
    runner = CliRunner()
    path = pathlib.Path(tmpdir).joinpath('test')

    # create a dummy trial
    result = runner.invoke(create, [str(path), '-n', num_patients, '-x'])
    assert result.exit_code == 0

    # simulate trial outcome files
    trial = Trial.read(path.joinpath('trial.yml'))

    outfiles = ['trial_data.RData', 'trial_outcome.Rmd', 'trial_outcome.html']
    for fn in outfiles:
        fn = trial.dir.joinpath(fn)
        fn.touch()

    # simulate present of patient_outcome.yml results
    for patient in trial:
        patient.dir.joinpath('patient_outcome.yml').touch()

    # ensure the desired files are present in the resulting archive
    with runner.isolated_filesystem():
        arxiv = pathlib.Path().joinpath('archive')
        result = runner.invoke(archive, [str(path), str(arxiv)])
        assert result.exit_code == 0

        # trial configuration should be copied
        assert arxiv.joinpath('trial.yml').exists()

        for patient in trial:
            # assert folder structure is replicated
            folder = arxiv.joinpath(os.path.basename(patient.dir))
            assert folder.exists()

            # assert configurations are copied
            for p in ['patient.yml', 'patient_outcome.yml']:
                assert folder.joinpath(p).exists()

    # ensure no failure without a subset of files, and,
    # ensure a failure when output folder already populated
    with runner.isolated_filesystem():
        for patient in trial:
            patient.dir.joinpath('patient_outcome.yml').unlink()

        for fn in outfiles:
            trial.dir.joinpath(fn).unlink()

        result = runner.invoke(archive, [str(path), str(arxiv)])
        assert result.exit_code == 0

        result = runner.invoke(archive, [str(path), str(arxiv)])
        assert result.exit_code == 2


@pytest.mark.parametrize('num_patients', [1, 2, 5])
def test_trial_archive_custom_file(tmpdir, num_patients):
    runner = CliRunner()
    path = pathlib.Path(tmpdir).joinpath('test')

    # create a dummy trial
    result = runner.invoke(create, [str(path), '-n', num_patients, '-x'])
    assert result.exit_code == 0

    # simulate trial outcome files
    trial = Trial.read(path.joinpath('trial.yml'))

    targets = ['subdir/custom_file_1.yml', 'subdir/custom_file_2.yml']

    # simulate present of patient_outcome.yml results
    for patient in trial:
        patient.dir.joinpath('patient_outcome.yml').touch()
        patient.dir.joinpath('subdir').mkdir()
        patient.dir.joinpath(targets[0]).touch()
        patient.dir.joinpath(targets[1]).touch()

    with runner.isolated_filesystem():
        arxiv = pathlib.Path().joinpath('archive')
        result = runner.invoke(
            archive,
            [str(path),
             str(arxiv), '-a', targets[0], '-a', targets[1]])
        assert result.exit_code == 0

        for patient in trial:
            folder = arxiv.joinpath(os.path.basename(patient.dir))
            assert folder.exists()

            # ensure custom targets are present
            for t in targets:
                assert folder.joinpath(t).exists()
