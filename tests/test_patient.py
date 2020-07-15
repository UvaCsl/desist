import filecmp
import pytest
import pathlib
import os
import yaml

from mock import patch

from workflow.patient import Patient, dict_to_xml
from workflow.utilities import get_git_hash, isct_module_path

@pytest.mark.parametrize("path", ["", "/home", pathlib.Path("/home")])
def test_init_patient_paths(path):
    p = Patient(path)
    assert p.dir == pathlib.Path(path).absolute()
    assert p.filename == "patient.yml"

def test_patient_full_path(tmp_path):
    p = Patient(tmp_path)
    assert p.dir == tmp_path
    assert p.full_path() == pathlib.Path(tmp_path).joinpath(p.filename)

def test_patient_repr(tmp_path):
    p = Patient(tmp_path)
    assert f"{type(p).__name__}({dict.__repr__(p)})" == p.__repr__()

@pytest.mark.parametrize("d", [{}, {"name": "name"}, {"name": "name", "id": "id"}])
def test_init_patient_from_dict(tmp_path, d):
    p = Patient(tmp_path, **d)

    # assert contents
    for k, v in d.items():
        assert p[k] == d[k]

    # assert path property
    assert p.dir == tmp_path

def test_init_patient_from_yaml(tmp_path):
    config = {"name": "name", "id": "id"}
    path = pathlib.Path(tmp_path).joinpath("patient.yml")
    with open(path, "w") as outfile:
        yaml.dump(config, outfile)

    p = Patient.from_yaml(path)

    assert p.dir == pathlib.Path(tmp_path).absolute()
    for k, v in p.items():
        assert v == config[k]

def test_init_patient_from_yaml_without_file(tmp_path):
    config = {"name": "name", "id": "id"}
    path = pathlib.Path(tmp_path).joinpath("patient.yml")
    with open(path, "w") as outfile:
        yaml.dump(config, outfile)

    path, fn = os.path.split(path)
    p = Patient.from_yaml(path)

    assert p.dir == pathlib.Path(tmp_path).absolute()
    for k, v in p.items():
        assert v == config[k]

def test_dump_patient_to_file(tmp_path):
    config = {"name": "name", "id": "id"}
    path = pathlib.Path(tmp_path).joinpath("config.yml")

    # reference
    with open(path, "w") as outfile:
        yaml.dump(config, outfile)

    # patient
    p = Patient(tmp_path, **config)
    p.to_yaml()

    assert filecmp.cmp(path, p.full_path())

@pytest.mark.parametrize("pid, seed", [(0, 1), (1, 2<<32 -1)])
def test_patient_set_defaults(tmp_path, pid, seed):
    patient = Patient(tmp_path)
    patient.set_defaults(pid, seed)

    assert patient['id'] == pid
    assert patient['status'] == False
    assert patient['random_seed'] == seed
    assert patient['git_sha'] == get_git_hash(isct_module_path())

    # validate the following keys are present: required for submodules
    required = [
            'git_sha',
            'id',
            'status',
            'random_seed',
            'HeartRate',
            'SystolePressure',
            'DiastolePressure',
            'MeanRightAtrialPressure',
            'StrokeVolume',
            ]

    for req in required:
        assert req in patient

@patch('workflow.utilities.isct_module_path', return_value="/")
def test_patient_set_defaults(tmp_path):
    patient = Patient(tmp_path)
    patient.set_defaults(1, 1)
    assert patient['git_sha'] == "not_found"

@pytest.mark.parametrize("pid, seed", [(-1, -1), (-1, 1), (1, -1), (0.0, 1), (1, 0.0)])
def test_patient_set_defaults_invalid(tmp_path, pid, seed):
    patient = Patient(tmp_path)
    with pytest.raises(AssertionError):
        patient.set_defaults(pid, seed)

def test_patient_set_defaults_return_self(tmp_path):
    patient = Patient(tmp_path)
    ref = patient.set_defaults(1, 1)
    assert ref == patient

def test_patient_empty_events(tmp_path):
    patient = Patient(tmp_path)
    assert patient.events() == []

def test_patient_add_events(tmp_path):
    patient = Patient(tmp_path)
    patient.set_events()

    assert isinstance(patient['events'], list)
    assert isinstance(patient['pipeline_length'], int)
    assert len(patient.events()) > 0
    assert len(patient.events()) == patient['pipeline_length']

    # assert defaults are present
    for event in patient.events():
        for required_key in ['event', 'id', 'status']:
            assert required_key in event

def test_patient_events_equal(tmp_path):
    patient = Patient(tmp_path)
    ref = patient.set_events()
    assert ref == patient # returns ref of itself
    assert patient.events() == patient['events'] # equal to dict

def test_patient_not_overwrite_existing_events(tmp_path):
    patient = Patient(tmp_path)
    patient['events'] = ['something']

    with pytest.raises(AssertionError):
        patient.set_events()
    assert patient.events() == ['something']

    patient.set_events(overwrite=True)
    assert patient.events() != []

def test_convert_config_yaml_to_xml(tmp_path):
    """Weakly test the conversion of YAML format towards XML."""

    # create xml document
    config = Patient(tmp_path).set_defaults(0, 1).set_events()
    config_xml = dict_to_xml(config)

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








