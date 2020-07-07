import pytest
import os

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



