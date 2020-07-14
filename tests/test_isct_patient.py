import pytest
import os
from mock import patch

from workflow.isct_patient import patient as patient_cmd
from workflow.isct_patient import create_patient_config, add_events_to_config
from workflow.isct_patient import config_yaml_to_xml
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

@pytest.mark.parametrize("pid, seed", [(0, 1), (1, 2<<32 -1)])
def test_create_patient_config(pid, seed):
    config = create_patient_config(pid, seed)
    assert config['id'] == pid
    assert config['status'] == False
    assert config['random_seed'] == seed

    # validate the following keys are present, as these are required for the
    # submodules, otherwise crashes.
    required = [
            'HeartRate',
            'SystolePressure',
            'DiastolePressure',
            'MeanRightAtrialPressure',
            'StrokeVolume',
            ]
    for req in required:
        assert req in config

@pytest.mark.parametrize("pid, seed", [(-1, -1), (-1, 0)])
def test_create_invalid_patient_config(pid, seed):
    with pytest.raises(AssertionError):
        config = create_patient_config(pid, seed)

def test_add_events_to_config():
    """Assert the events are filled with the right data format."""
    # add contents to emtpy dict
    config = {}
    config = add_events_to_config(config)

    # must be present
    for k in ['events', 'pipeline_length']:
        assert k in config

    # need to be list and int
    assert isinstance(config['events'], list)
    assert isinstance(config['pipeline_length'], int)

    # check events are non-empty
    events = config['events']
    assert len(events) > 0
    assert len(events) == config['pipeline_length']

    # check analysis steps are present
    for i in range(len(events)):
        assert 'event' in events[i]
        assert 'id' in events[i]
        assert 'status' in events[i]

def test_add_events_fails_on_existing_events():
    """Assert without `overwrite=True` events are not overwritten"""
    config = {"events": True}
    with pytest.raises(SystemExit):
        config = add_events_to_config(config)

    config = add_events_to_config(config, overwrite=True)
    assert 'events' in config
    assert len(config['events']) > 1
    assert len(config['events']) == config['pipeline_length']

def test_convert_config_yaml_to_xml():
    """Weakly test the conversion of YAML format towards XML."""

    config = create_patient_config(0, 1)
    config = add_events_to_config(config)

    # perform mapping to xml
    config_xml = config_yaml_to_xml(config)

    # check basic items
    assert config_xml.tag == 'virtualPatient'

    # check patient
    vp = config_xml.findall('Patient')
    assert vp is not None
    assert len(vp) == 1

    # check some contents of the <Patient>
    vp = vp[0]
    for k in ['id', 'events', 'random_seed', 'HeartRate']:
        element = vp.findall(k)
        assert element is not None
        assert len(element) == 1

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

