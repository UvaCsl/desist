import pytest
import os
from mock import patch

from workflow.patient import Patient
from workflow.isct_patient import patient as patient_cmd
from workflow.isct_trial import trial
from tests.test_isct_trial import trial_directory

def test_patient_no_configuration(trial_directory):
    path = trial_directory
    with pytest.raises(SystemExit):
        patient_cmd(f"patient create {path} --config-only".split())

@pytest.mark.parametrize("arg", [("--id 1.0"), ("--seed 1.0")])
def test_patient_invalid_schema(trial_directory, arg):
    path = trial_directory
    with pytest.raises(SystemExit):
        patient_cmd(f"patient create {path} {arg}".split())

def test_patient_already_exist(trial_directory):
    path = trial_directory
    trial(f"trial create {path}".split())
    assert os.path.isdir(path)

    with pytest.raises(SystemExit):
        patient_cmd(f"patient create {path}".split())

    # overwrite should work
    patient_cmd(f"patient create {path} -f".split())

def test_patient_create_yaml_no_docker(trial_directory, mocker):
    path = trial_directory
    trial(f"trial create {path}".split())
    assert os.path.isdir(path)

    mocker.patch('shutil.which', return_value=None)
    patient_cmd(f"patient create {path} -f".split())
    assert os.path.isfile(path.joinpath("patient_000/patient.yml"))


def test_patient_run_dry(trial_directory, mocker):
    path = trial_directory
    patient = path.joinpath("patient_000")
    trial(f"trial create {path} -n 1".split())

    mocker.patch("shutil.which", return_value="/mocker/bin/docker")

    # only runs it, does not really assert anything
    patient_cmd(f"patient run {patient} -x".split())

def test_patient_run_invalid_path(trial_directory):
    path = trial_directory.joinpath("not_existing")
    with pytest.raises(SystemExit):
        patient_cmd(f"patient run {path} -x".split())

