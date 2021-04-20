import os
import pathlib
import pytest

from desist.isct.trial import Trial, ParallelTrial, trial_config
from desist.isct.patient import Patient, LowStoragePatient
from desist.isct.runner import Logger
from desist.isct.utilities import OS

from test_runner import DummyRunner


def test_trial(tmpdir):
    trial = Trial(tmpdir)
    assert trial.path.parent == tmpdir
    assert trial.path.name == trial_config


def test_trial_exists(tmpdir):
    path = pathlib.Path(tmpdir)
    with pytest.raises(FileNotFoundError):
        Trial.read(path.joinpath(trial_config))

    trial = Trial(path, runner=Logger)
    trial.write()
    Trial.read(trial.path)


@pytest.mark.parametrize('sample_size', [1, 10])
def test_trial_length(tmpdir, sample_size):
    trial = Trial(tmpdir, sample_size, runner=Logger())
    trial.create()
    assert len(trial) == sample_size


@pytest.mark.parametrize('config', [{}, {
    'a': 1
}, {
    'sample_size': 10
}, {
    'random_seed': 10
}])
def test_trial_config(tmpdir, config):
    path = pathlib.Path(tmpdir).joinpath(trial_config)
    trial = Trial(path, config=config, runner=Logger)
    assert trial.get('sample_size') == config.get('sample_size', 1)
    assert trial.get('random_seed') == config.get('random_seed', 1)
    for k in config:
        assert trial.get(k) == config.get(k)


@pytest.mark.parametrize('platform', [OS.MACOS, OS.LINUX])
@pytest.mark.parametrize('sample_size', list(range(1, 5)))
def test_trial_create(mocker, tmpdir, sample_size, platform):
    mocker.patch('desist.isct.utilities.OS.from_platform', return_value=platform)

    trial = Trial(tmpdir, sample_size, runner=Logger())
    trial.create()

    assert os.path.isdir(trial.path.parent)
    assert os.path.isfile(trial.path)
    assert trial.get('sample_size') == sample_size

    for i in range(trial.get('sample_size')):
        patient = Patient(trial.dir, idx=i)
        assert os.path.isdir(patient.path.parent)

    read = Trial.read(trial.path)
    for k, v in trial.items():
        assert read.get(k) == v


@pytest.mark.parametrize('platform', [OS.MACOS, OS.LINUX])
@pytest.mark.parametrize('sample_size', list(range(1, 5)))
def test_trial_sample(mocker, tmpdir, sample_size, platform):
    mocker.patch('desist.isct.utilities.OS.from_platform', return_value=platform)

    # record the outcome
    runner = DummyRunner(write_config=True)

    # initialise the trial
    trial = Trial(tmpdir, sample_size, runner=runner)
    trial.create()

    assert os.path.isdir(trial.path.parent)
    assert os.path.isfile(trial.path)
    assert trial.get('sample_size') == sample_size

    # all patients are sampled
    for patient in trial:
        assert os.path.basename(patient.dir) in runner

    runner.clear()

    # add some more patients
    for i in range(sample_size, 2 * sample_size):
        trial.append_patient(i)
    assert trial.get('sample_size') == 2 * sample_size

    # populate patients
    trial.sample_virtual_patient(sample_size, 2 * sample_size)

    patients = [os.path.basename(patient.dir) for patient in trial]
    assert all([p not in runner for p in patients[:sample_size]])
    assert all([p in runner for p in patients[sample_size:]])


@pytest.mark.parametrize('sample_size', list(range(1, 5)))
def test_trial_sample_empty_set(tmpdir, sample_size):
    trial = Trial(tmpdir, sample_size, runner=Logger())
    with pytest.raises(AssertionError):
        trial.sample_virtual_patient(1 + sample_size, sample_size)
    with pytest.raises(AssertionError):
        trial.sample_virtual_patient(sample_size, sample_size)


@pytest.mark.parametrize('platform', [OS.MACOS, OS.LINUX])
@pytest.mark.parametrize('sample_size', [5])
def test_trial_outcome(mocker, tmpdir, sample_size, platform):
    mocker.patch('desist.isct.utilities.OS.from_platform', return_value=platform)

    runner = DummyRunner(write_config=True)
    trial = Trial(tmpdir, sample_size, runner=runner)
    trial.create()

    assert os.path.isdir(trial.path.parent)
    assert os.path.isfile(trial.path)

    # evaluate outcome; only check the emitted command
    runner.clear()
    trial.outcome()

    # assert some expected snippets are present
    for substring in ['run', f'{trial.dir}:/trial', 'trial-outcome']:
        assert substring in runner, f'missing {substring} in {runner}'


@pytest.mark.parametrize('keep_files, patient_cls',
                         [(True, Patient), (False, LowStoragePatient)])
@pytest.mark.parametrize('trial_cls', [Trial, ParallelTrial])
@pytest.mark.parametrize('platform', [OS.MACOS, OS.LINUX])
def test_trial_run(mocker, tmpdir, trial_cls, platform, keep_files,
                   patient_cls):
    """Ensure trial run does not fail, capture commands inside runner."""
    mocker.patch('desist.isct.utilities.OS.from_platform', return_value=platform)

    sample_size = 5
    runner = DummyRunner(write_config=True)
    trial = trial_cls(tmpdir,
                      sample_size,
                      runner=runner,
                      keep_files=keep_files)

    trial.create()
    assert os.path.isdir(trial.path.parent)
    assert os.path.isfile(trial.path)

    # these tests could be more extensive
    trial.run()
    assert 'run' in runner
    if trial_cls == ParallelTrial:
        assert 'desist' in runner

    for patient in trial:
        assert f'{patient.path.parent}' in runner
        assert isinstance(patient, patient_cls)

    # reset output and ensure skippable patients are skipped
    runner.clear()

    # Parallel is not actually evaluated, i.e. we do not go through gnu
    # parallel in tests, thus we manually set it to completed
    if trial_cls == ParallelTrial:
        for patient in trial:
            patient.completed = True
            patient.write()

    trial.run(skip_completed=True)
    for patient in trial:
        assert patient.completed
        assert f'{patient.path.parent}' not in runner


def test_trial_container_path(tmpdir):
    singularity = pathlib.Path(tmpdir).joinpath('singularity/')
    config = {'container-path': str(singularity)}
    trial = Trial(tmpdir, config=config)

    # should be invalid: the container path does _not_ exist
    assert trial.invalid_container_path()

    # should be valid: the container path _does_ exist
    os.makedirs(singularity)
    assert not trial.invalid_container_path()
