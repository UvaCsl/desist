from click.testing import CliRunner

import pathlib
import pytest
import os

from desist.cli.trial import create, append, run, list_key, outcome, archive
from desist.cli.trial import reset, clean
from desist.isct.config import Config
from desist.isct.trial import Trial, trial_config
from desist.isct.utilities import OS, MAX_FILE_SIZE, CleanFiles

from tests.isct.test_utilities import create_dummy_file, default_criteria_file


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
            assert f'trial/{patient.name}' in result.output


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
@pytest.mark.parametrize('key', ['events', 'labels'])
def test_trial_from_criteria_file_with_incomplete_events(tmpdir, n, key):
    runner = CliRunner()
    path = pathlib.Path('test')
    with runner.isolated_filesystem():
        criteria = Config('{tmpdir}/criteria.yml', {
            'sample_size': n,
            'testkey': True,
            key: True
        })
        criteria.write()
        assert os.path.exists(criteria.path)

        result = runner.invoke(
            create,
            [str(path), '-c', str(criteria.path), '-x'])
        assert result.exit_code == 2
        assert 'Key error in criteria file' in result.output


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
            assert f'trial/{patient.name}' in result.output

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
                assert f'trial/{patient.name}' in result_c.output
            else:
                assert f'trial/{patient.name}' in result_a.output


@pytest.mark.parametrize('keep_files', [True, False])
@pytest.mark.parametrize('platform', [OS.MACOS, OS.LINUX])
@pytest.mark.parametrize('parallel', [None, '--parallel', '--qcg'])
@pytest.mark.parametrize('num', [1, 2, 5])
def test_trial_run(mocker, tmpdir, keep_files, platform, num, parallel):
    mocker.patch('desist.isct.utilities.OS.from_platform',
                 return_value=platform)

    if keep_files:
        keep_cmd = ['--clean-files', 'none']
    else:
        keep_cmd = ['--clean-files', CleanFiles.LARGE.value]

    runner = CliRunner()
    path = pathlib.Path(tmpdir).joinpath('test')
    with runner.isolated_filesystem():
        result = runner.invoke(create, [
            str(path), '-n', num, '-x', '-c', default_criteria_file(tmpdir)
        ])
        assert result.exit_code == 0

        cmd = [str(path)]
        cmd = cmd if parallel is None else cmd + [parallel]
        cmd = cmd + ['-x']
        cmd = cmd + keep_cmd

        # create a large file in one of the patients
        trial = Trial.read(path.joinpath(trial_config))

        large_file = list(trial)[0].dir.joinpath('large-file')
        create_dummy_file(large_file, MAX_FILE_SIZE + 10)
        assert large_file.exists()

        result = runner.invoke(run, cmd)
        assert result.exit_code == 0

        for i in range(num):
            assert f'patient_{i:05}' in result.output

        print('result:', result.output)

        if parallel is None:
            for k in ['docker', 'run']:
                assert k in result.output
            assert keep_files == large_file.exists()
        else:
            assert 'docker' not in result.output
            assert all(cmd in result.output for cmd in keep_cmd)


@pytest.mark.parametrize('parallel', ['--parallel', '--qcg'])
@pytest.mark.parametrize('platform', [OS.MACOS, OS.LINUX])
def test_trial_run_parallel_singularity(mocker, tmpdir, platform, parallel):
    mocker.patch('desist.isct.utilities.OS.from_platform',
                 return_value=platform)

    runner = CliRunner()
    path = pathlib.Path(tmpdir).joinpath('test')

    local = pathlib.Path(tmpdir).joinpath('local')
    remote = pathlib.Path(tmpdir).joinpath('remote')

    for p in (local, remote):
        os.makedirs(p)

    with runner.isolated_filesystem():
        args = [str(path), '-x', '-s', str(local)]
        result = runner.invoke(create, args)
        assert result.exit_code == 0

        result = runner.invoke(run, [str(path), parallel, '-x'])
        assert result.exit_code == 0

        # assert the local directory is used by default, i.e. the one specified
        # on creation of the trial
        trial = Trial.read(path.joinpath(trial_config))
        for i in range(len(trial)):
            assert f'patient_{i:05}' in result.output
        assert 'docker' not in result.output
        assert '--container-path' in result.output
        assert f'{local}' in result.output

        # assert the remote directory is used when specific manually.
        cmd = [str(path), parallel, '-x', '-c', str(remote)]
        result = runner.invoke(run, cmd)
        for i in range(len(trial)):
            assert f'patient_{i:05}' in result.output
        assert result.exit_code == 0
        assert '--container-path' in result.output
        assert f'{local}' not in result.output
        assert f'{remote}' in result.output


@pytest.mark.parametrize('platform', [OS.MACOS, OS.LINUX])
@pytest.mark.parametrize('parallel', [None, '--parallel', '--qcg'])
@pytest.mark.parametrize('num', [1, 2, 5])
def test_trial_run_missing_config(mocker, tmpdir, platform, num, parallel):
    mocker.patch('desist.isct.utilities.OS.from_platform',
                 return_value=platform)

    runner = CliRunner()
    path = pathlib.Path(tmpdir).joinpath('test')
    with runner.isolated_filesystem():
        result = runner.invoke(create, [
            str(path), '-n', num, '-x', '-c', default_criteria_file(tmpdir)
            ]
        )
        assert result.exit_code == 0

        cmd = [str(path)]
        cmd = cmd if parallel is None else cmd + [parallel]
        cmd = cmd + ['-x']

        # remove the config
        trial = Trial.read(path.joinpath(trial_config))
        trial.path.unlink()
        assert not trial.path.exists()

        # ensure runs as usual, as it can fallback on extracting the patients
        # from the subdirectory, even when the trial config itself is missing
        result = runner.invoke(run, cmd)
        assert result.exit_code == 0

        for i in range(num):
            assert f'patient_{i:05}' in result.output

        if parallel is None:
            for k in ['docker', 'run']:
                assert k in result.output
        else:
            assert 'docker' not in result.output


@pytest.mark.parametrize('platform', [OS.MACOS, OS.LINUX])
def test_trial_run_container_path(mocker, tmpdir, platform):
    mocker.patch('desist.isct.utilities.OS.from_platform',
                 return_value=platform)

    runner = CliRunner()
    path = pathlib.Path(tmpdir).joinpath('test')

    local_path = pathlib.Path(tmpdir).joinpath('local')
    remote_path = pathlib.Path(tmpdir).joinpath('remote')

    for p in [local_path, remote_path]:
        os.makedirs(p)

    with runner.isolated_filesystem():
        # create the trials with respect to the local trial directory
        cmd = [str(path), '-n', 1, '-x', '-s', str(local_path)]
        result = runner.invoke(create, cmd)
        assert result.exit_code == 0

        # ensure the local path is not present: mimick remote running
        os.rmdir(local_path)

        # this command must now fails: the local container path is not
        # present on the system, thus `assert_container_path` raises an error.
        result = runner.invoke(run, [str(path), '-x'])
        assert result.exit_code == 2

        # explicity providing the alternative path to override the container
        # path should allow the run to work fine.
        result = runner.invoke(run, [str(path), '-x', '-c', str(remote_path)])
        assert result.exit_code == 0


@pytest.mark.parametrize('num_patients', [5])
def test_trial_outcome(tmpdir, num_patients):
    runner = CliRunner()
    path = pathlib.Path('test')
    with runner.isolated_filesystem(temp_dir=tmpdir) as td:
        result = runner.invoke(create, [str(path), '-n', num_patients, '-x'])
        assert result.exit_code == 0

        trial = Trial.read(path.joinpath(trial_config))
        result = runner.invoke(outcome, [str(path), '-x'])
        assert result.exit_code == 0
        assert f'{trial.dir}:/trial' in result.output

        result = runner.invoke(outcome, [str(path), '-x', '-c', 'host:local'])
        assert result.exit_code == 0
        assert '--compare' in result.output
        assert f'-v {td}/host:local' in result.output


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

        result = runner.invoke(list_key, [str(path), 'events'])
        assert result.exit_code == 2
        assert 'not supported' in result.output


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


@pytest.mark.parametrize('platform', [OS.MACOS, OS.LINUX])
def test_trial_reset(mocker, tmpdir, platform):
    mocker.patch('desist.isct.utilities.OS.from_platform',
                 return_value=platform)

    runner = CliRunner()
    path = pathlib.Path(tmpdir).joinpath('test')

    # create a dummy trial
    result = runner.invoke(create, [str(path), '-n', '5', '-x'])
    assert result.exit_code == 0

    # set all patients to completed and create dummy file to be removed
    trial = Trial.read(path.joinpath('trial.yml'))
    for patient in trial:
        patient.dir.joinpath('test_file.txt').touch()
        patient.completed = True
        patient.write()

    for patient in trial:
        assert patient.completed
        assert patient.dir.joinpath('test_file.txt').exists()

    with runner.isolated_filesystem():
        result = runner.invoke(reset, [str(path), '-r', 'test_file.txt'])
        assert result.exit_code == 0

        for patient in trial:
            assert not patient.completed
            assert not patient.dir.joinpath('test_file.txt').exists()


@pytest.mark.parametrize('mode', [CleanFiles.ALL, CleanFiles.LARGE])
@pytest.mark.parametrize('size_delta', [+10, -10])
def test_trial_clean(tmpdir, mode, size_delta):
    runner = CliRunner()
    path = pathlib.Path(tmpdir).joinpath('test')
    with runner.isolated_filesystem():
        result = runner.invoke(create, [str(path), '-n', 10, '-x'])
        assert result.exit_code == 0

        trial = Trial.read(path.joinpath(trial_config))

        large_file = list(trial)[0].dir.joinpath('large-file')
        create_dummy_file(large_file, MAX_FILE_SIZE + size_delta)

        result = runner.invoke(clean, [str(path), mode.value])
        assert result.exit_code == 0

        if mode == CleanFiles.ALL:
            assert not large_file.exists()

        if mode == CleanFiles.LARGE:
            assert large_file.exists() == (size_delta < 0)


def test_trial_parallel_qcg(tmpdir):
    runner = CliRunner()
    path = pathlib.Path(tmpdir).joinpath('test')
    with runner.isolated_filesystem():
        result = runner.invoke(create, [str(path), '-n', 10, '-x'])
        assert result.exit_code == 0

        result = runner.invoke(run, [str(path), '--parallel', '--qcg'])
        assert result.exit_code == 2
        assert 'Ambiguous' in result.output
