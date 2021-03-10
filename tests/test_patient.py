import os
import pathlib
import pytest


from isct.utilities import OS
from isct.patient import Patient, patient_config, LowStoragePatient
from test_runner import DummyRunner


def test_patient(tmpdir):
    path = pathlib.Path(tmpdir)
    patient = Patient(tmpdir, idx=0)
    assert patient.path.parent == path.joinpath('patient_00000')
    assert patient.path.parent.parent == path


def test_patient_read_missing(tmpdir):
    with pytest.raises(SystemExit):
        Patient.read(tmpdir)


def test_patient_read_prefix(tmpdir):
    path = pathlib.Path(tmpdir)
    prefix, idx = 'test', 1
    patient = Patient(path, idx=idx, prefix='test')
    assert patient.path == path.joinpath(f'{prefix}_{idx:05}/patient.yml')
    patient.write()

    patient = Patient.read(patient.path)
    assert patient.path == path.joinpath(f'{prefix}_{idx:05}/patient.yml')


def test_patient_exists(tmpdir):
    with pytest.raises(SystemExit):
        path = pathlib.Path(tmpdir).joinpath(patient_config)
        Patient.read(path)

    patient = Patient(tmpdir, 0)
    patient.write()
    assert os.path.isfile(patient)

    Patient.read(patient.path)


@pytest.mark.parametrize('idx, prefix', [(10, 'test')])
@pytest.mark.parametrize('config', [{}, {'a': 1}])
def test_patient_config(tmpdir, idx, prefix, config):
    path = pathlib.Path(tmpdir).joinpath(patient_config)
    patient = Patient(path, idx=idx, prefix=prefix, config=config)
    assert patient.get('id') == idx
    assert patient.get('prefix') == prefix
    for k in config:
        assert patient.get(k) == config.get(k)


def test_patient_create(tmpdir):
    patient = Patient(tmpdir)
    patient.create()
    assert os.path.isdir(patient.path.parent)
    assert os.path.isfile(patient.path)


def test_patient_run(tmpdir):
    path = pathlib.Path(tmpdir)
    patient = Patient(path, runner=DummyRunner())
    patient.create()

    runner = DummyRunner()
    patient = Patient.read(patient.path, runner=runner)

    patient.run()
    assert f'{patient.path.parent}:/patient' in runner
    assert not patient.completed, "verbose runner should not update the config"

    runner.write_config = True
    patient.run()
    assert patient.completed, "non-verbose runner should update the config"


@pytest.mark.parametrize('platform', [OS.MACOS, OS.LINUX])
def test_patient_failed_event(mocker, tmpdir, platform):
    """Ensure the simulation raises `AssertionError` for failed event."""
    mocker.patch('isct.utilities.OS.from_platform', return_value=platform)

    path = pathlib.Path(tmpdir)
    patient = Patient(path, runner=DummyRunner(write_config=True))
    patient.create()

    # mock runner to succeed
    mocker.patch('isct.docker.Docker.run', return_value=True)
    mocker.patch('isct.singularity.Singularity.run', return_value=True)
    patient.run()
    assert patient.completed

    # mock runner to fail
    mocker.patch('isct.docker.Docker.run', return_value=False)
    mocker.patch('isct.singularity.Singularity.run', return_value=False)
    with pytest.raises(AssertionError):
        patient.run()


def test_lowstorage_patient(tmpdir):
    path = pathlib.Path(tmpdir)
    patient = Patient(path, runner=DummyRunner())
    patient.create()
    ls_patient = LowStoragePatient.from_patient(patient)
    assert ls_patient == patient
    assert ls_patient.path == patient.path
    assert ls_patient.runner == patient.runner


def test_patient_reset(tmpdir):
    path = pathlib.Path(tmpdir)
    patient = Patient(path, runner=DummyRunner(write_config=True))
    patient.completed = True
    assert patient.completed

    # reset to uncompleted
    patient.reset()
    assert not patient.completed
