import docopt
import pytest
import schema
import os
import yaml

from mock import patch

from workflow.patient import Patient
from workflow.isct_container import container
from tests.test_isct_trial import trial_directory
from workflow.isct_container import form_container_command
from workflow.isct_trial import trial as trial_cmd

@pytest.mark.parametrize("arg", ([1, 1.0, "/novalidpath", None]))
def test_container_invalid_arguments(arg):
    with pytest.raises(SystemExit):
        if arg is None:
            container("")
        else:
            container(f"container build {arg}".split())

@pytest.mark.parametrize("arg", (["-vx"]))
def test_container_valid_path(trial_directory, arg):
    path = trial_directory.absolute()
    os.mkdir(path.absolute())

    assert os.path.isdir(path.absolute())
    container(f"container build {path} {arg}".split())

    paths = " ".join([str(path) for i in range(10)])
    container(f"container build {paths} {arg}".split())

def test_form_docker_command(trial_directory):
    tag = "place_clot"
    patient = trial_directory
    event_id = 0

    cmd = form_container_command(tag, patient, event_id)
    res = ["docker", "run", "-v", f"{patient}:/patient", f"{tag}", "handle_event", "--patient=/patient/config.xml", "--event", f"{event_id}"]

    # same command length
    assert len(cmd) == len(res)

    # identical command contents
    for (c, r) in zip(cmd, res):
        assert c == r

def test_container_no_docker(tmp_path, mocker):
    # ensure it does not fail.. that's all
    path = tmp_path
    assert os.path.isdir(path)
    mocker.patch('shutil.which', return_value=None)
    container(f"container build {path}".split())

def test_run_container_invalid_path(trial_directory):
    with pytest.raises(SystemExit):
        container(f"container run tag {trial_directory} 1 -x".split())

def test_run_container_exit_without_docker(tmp_path, mocker):
    mocker.patch('shutil.which', return_value=None)
    with pytest.raises(SystemExit):
        container(f"container run tag {tmp_path} 1 -x".split())

def test_run_container_valid_path(trial_directory, mocker):
    # create config file
    path = trial_directory
    trial_cmd(f"trial create {path} -n 1".split())
    patient = path.joinpath("patient_000")

    mocker.patch("shutil.which", return_value="/mocker/bin/docker")

    # exit if tag does not exit
    with pytest.raises(AssertionError):
        container(f"container run tag {patient} 1 -x".split())

    # mock tag exists
    config = {'events': [{'event': "tag", 'id': 1}]}
    with open(patient.joinpath("patient.yml"), "w") as configfile:
        yaml.dump(config, configfile)

    container(f"container run tag {patient} 1 -x".split())

@patch('shutil.which', return_value="/mocker/bin/docker")
@patch('subprocess.run', return_value=True)
def test_run_container_marks_event_as_complete(mock_which, mock_run, trial_directory):
    # create config
    path = trial_directory
    patient = Patient(path.joinpath("patient_000"))
    os.makedirs(patient.dir)
    patient.set_events()
    patient.to_yaml()

    # run the first dummy event (note: subprocess.run mocks the docker call)
    event = patient.events()[0]
    print(f"container run {event['event']} {patient.dir} {event['id']}".split())
    container(f"container run {event['event']} {patient.dir} {event['id']}".split())

    # make sure patient config still exist
    assert Patient.path_is_patient(patient.dir)

    # ensure the first status is now set to true
    patient = Patient.from_yaml(patient.dir)
    assert patient.events()[0]['status']
