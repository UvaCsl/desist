import os
import pathlib
import pytest

from isct.trial import Trial, trial_config
from isct.patient import Patient


def test_trial(tmpdir):
    trial = Trial(tmpdir)
    assert trial.path.parent == tmpdir
    assert trial.path.name == trial_config


def test_trial_exists(tmpdir):
    path = pathlib.Path(tmpdir)
    with pytest.raises(SystemExit):
        Trial.read(path.joinpath(trial_config))

    trial = Trial(path)
    trial.write()
    Trial.read(trial.path)


@pytest.mark.parametrize('config', [{}, {
    'a': 1
}, {
    'sample_size': 10
}, {
    'random_seed': 10
}])
def test_trial_config(tmpdir, config):
    path = pathlib.Path(tmpdir).joinpath(trial_config)
    trial = Trial(path, config=config)
    assert trial.get('sample_size') == config.get('sample_size', 1)
    assert trial.get('random_seed') == config.get('random_seed', 1)
    for k in config:
        assert trial.get(k) == config.get(k)


@pytest.mark.parametrize('sample_size', list(range(5)))
def test_trial_create(tmpdir, sample_size):
    trial = Trial(tmpdir, sample_size)
    trial.create()

    assert os.path.isdir(trial.path.parent)
    assert os.path.isfile(trial.path)

    for i in range(trial.get('sample_size')):
        patient = Patient(trial.path, idx=i)
        #assert os.path.isdir(patient.path.parent)
        # FIXME: these paths are focked
        #assert os.path.isfile(patient.path)

    read = Trial.read(trial.path)
    for k, v in trial.items():
        assert read.get(k) == v

