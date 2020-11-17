import docopt
import pytest
import schema
import subprocess
import os
import yaml

from subprocess import Popen

from mock import patch, MagicMock

from isct.patient import Patient
from isct.isct_container import container
from isct.utilities import run_and_stream
from tests.test_isct_trial import trial_directory
from isct.isct_container import form_container_command
from isct.isct_trial import trial as trial_cmd
from tests.test_utilities import log_subprocess_run, mock_check_output


# This newpopen mocks a popen object that holds some data inside its .stdout
# attribute. This is to mock statements as `with subprocess.Popen` and of which
# the `.stdout` attribute is afterwards emtied towards the log. This class
# provides the required functions to mimic the same behaviour, where the command
# is something meaningless rather than a call to Docker/Singularity
class newpopen(object):
    def __init__(self, returncode=0):
        # evaluate some silly process to mock the output
        proc = subprocess.Popen(['echo', 'hello'], stdout=subprocess.PIPE,
                encoding='utf-8', universal_newlines=True)
        proc.wait()
        self.stdout = proc.stdout
        self.returncode = returncode

    def __enter__(self):
        return self

    def __exit__(self, a, b, c):
        pass

@pytest.mark.parametrize("arg", ([1, 1.0, "/novalidpath", None]))
def test_container_invalid_arguments(arg):
    with pytest.raises(SystemExit):
        if arg is None:
            container("")
        else:
            container(f"container build {arg}".split())

@pytest.mark.parametrize("arg", (["-vx", "--gnu-parallel", "-v"]))
def test_container_valid_path(trial_directory, arg, mocker):
    path = trial_directory.absolute()
    os.mkdir(path.absolute())

    # mock the runner to prevent attempting to build actual images during tests
    mocker.patch('subprocess.Popen', return_value=newpopen())

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

def test_run_missing_container_exit(trial_directory):
    path = trial_directory.joinpath("patient_000")
    os.makedirs(path)
    p = Patient(path, **{"name": "name", "id": "id"})
    p.to_yaml()
    with pytest.raises(SystemExit):
        container(f"container run tag {path} 1 -v".split())

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
    config = {'labels': {'no-tag': 'no-tag', 'tag': 'tag'}, 'events': [
            {'event': 'baseline',
            'models': [{'label': 'no-tag'}, {'label': 'tag'}]}]}
    with open(patient.joinpath("patient.yml"), "w") as configfile:
        yaml.dump(config, configfile)

    container(f"container run tag {patient} 1 -x".split())

@pytest.mark.usefixtures('mock_check_output')
@patch('subprocess.run', return_value=True)
@patch('shutil.which', return_value="/mocker/bin/docker")
def test_run_container_marks_event_as_complete(mock_which, mock_run, trial_directory, mocker):
    # create config
    path = trial_directory
    patient = Patient(path.joinpath("patient_000"))
    os.makedirs(patient.dir)
    patient.set_models()
    patient.to_yaml()

    # mock the subprocess popen by some dummy command
    mocker.patch('subprocess.Popen', return_value=newpopen())

    # run the first dummy event (note: subprocess.run mocks the docker call)
    event = next(patient.models)
    container(f"container run {event['container']} {patient.dir} 0".split())

    # make sure patient config still exist
    assert Patient.path_is_patient(patient.dir)

    # ensure the first status is now set to true
    patient = Patient.from_yaml(patient.dir)
    assert patient.completed == 0

@pytest.mark.usefixtures('mock_check_output')
@patch('subprocess.run', return_value=True)
@patch('shutil.which', return_value="/mocker/bin/docker")
def test_terminate_failed_container(mock_which, mock_run,
        trial_directory, mocker):
    # create config
    path = trial_directory
    patient = Patient(path.joinpath("patient_000"))
    os.makedirs(patient.dir)
    patient.set_models()
    patient.to_yaml()

    # assert patient terminate=True on non-zero exit code
    mocker.patch('subprocess.Popen', return_value=newpopen(returncode=1))
    event = next(patient.models)
    container(f"container run {event['container']} {patient.dir} 0".split())

    patient = Patient.from_yaml(patient.dir)
    assert patient.terminated
    assert patient.completed < 0

    # assert container can run; no failer after marked failed
    container(f"container run {event['container']} {patient.dir} 0".split())
