from click.testing import CliRunner
import pathlib
import pytest
import os

from isct.cli_trial import create, append, run
from isct.trial import Trial, trial_config

# FIXME: `dry` run does still create all directories though...
# FIXME: these tets still have issues with paths...


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

        for patient in trial.patients:
            assert f'trial/{patient}' in result.output


@pytest.mark.parametrize('n', [1, 5])
def test_trial_append(tmpdir, n):
    runner = CliRunner()
    path = pathlib.Path(tmpdir)
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


@pytest.mark.parametrize('num_patients', [2])
def test_trial_run(tmpdir, num_patients):
    runner = CliRunner()
    path = pathlib.Path(tmpdir)
    with runner.isolated_filesystem():
        result = runner.invoke(create, [str(path), '-n', num_patients], '-x')
        assert result.exit_code == 0

        result = runner.invoke(run, [str(path), '-x'])
        assert result.exit_code == 0

        for i in range(num_patients):
            assert f'patient_{i:05}' in result.output

        for k in ['docker', 'run']:
            assert k in result.output
