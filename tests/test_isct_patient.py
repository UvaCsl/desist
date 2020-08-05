import pytest
import os
import yaml
from mock import patch

from workflow.patient import Patient
from workflow.isct_patient import patient as patient_cmd
from workflow.isct_patient import patient_validate
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

def test_patient_create_yaml_additional_patient(trial_directory):
    path = trial_directory
    trial(f"trial create {path} -n 1".split())
    assert os.path.isdir(path)

    patient_cmd(f"patient create {path} -f --id=1".split())
    assert os.path.isfile(path.joinpath("patient_001/patient.yml"))

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
    patient_cmd(f"patient run {patient} -x --singularity .".split())

def test_patient_run_invalid_path(trial_directory):
    path = trial_directory.joinpath("not_existing")
    with pytest.raises(SystemExit):
        patient_cmd(f"patient run {path} -x".split())

def test_patient_validate_invalid_path(trial_directory):
    path = trial_directory.joinpath("not_existing")
    with pytest.raises(SystemExit):
        patient_cmd(f"patient validate {path}".split())

def test_patient_validate_config(trial_directory):
    from tests.test_patient import document
    # valid patient, with a valid configuration file
    p0 = trial_directory.joinpath("patient_0")
    os.makedirs(p0)
    config = yaml.load(document, yaml.SafeLoader)
    patient_0 = Patient(p0, **config)
    patient_0.to_yaml()

    # These tests access the `patient_validate` function directly, i.e. they
    # do not pass through `patient` first. This is to capture the output for the
    # `patient_validate` function, which is normally hidden when access via the
    # `patient` command. However, internally, we can get access to its output
    # and validate if its behaviour is correct. It is a bit clumsy, but should
    # be sufficient for a basic test.
    import workflow.isct_patient as mypatient
    import docopt

    argv = docopt.docopt(mypatient.__doc__, argv=f"patient validate {patient_0.dir}")
    res = patient_validate(argv)
    assert all([b for (r, b) in res])

    # invalid patient
    p1 = trial_directory.joinpath("patient_1")
    os.makedirs(p1)
    del config['random_seed']
    patient_1 = Patient(p1, **config)
    patient_1.to_yaml()

    argv = docopt.docopt(mypatient.__doc__, argv=f"patient validate {patient_1.dir}")
    res = patient_validate(argv)
    assert not all([b for (r, b) in res])

    ## fail when one of the patients is invalid
    argv = docopt.docopt(mypatient.__doc__, argv=f"patient validate {patient_0.dir} {patient_1.dir}")
    res = patient_validate(argv)
    assert not all([b for (r, b) in res])
