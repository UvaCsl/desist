import os
import pathlib
import pytest


from isct.patient import Patient, patient_config
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
