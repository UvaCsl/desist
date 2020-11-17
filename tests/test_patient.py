import filecmp
import pytest
import pathlib
import os
import yaml

from mock import patch

from tests.test_isct_trial import trial_directory
from isct.patient import Patient, dict_to_xml, Model, Event
from isct.patient import patients_from_trial
from isct.utilities import get_git_hash, isct_module_path

@pytest.mark.parametrize("path", ["", "/home", pathlib.Path("/home")])
def test_init_patient_paths(path):
    p = Patient(path)
    assert p.dir == pathlib.Path(path).absolute()
    assert p.filename == "patient.yml"
    assert p.path == pathlib.Path(path).absolute().joinpath("patient.yml")

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

@patch('isct.utilities.isct_module_path', return_value="/")
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
    assert list(patient.models) == []

def test_patient_add_events(tmp_path):
    patient = Patient(tmp_path)
    patient.set_models()

    assert isinstance(patient['events'], list)
    assert isinstance(patient['pipeline_length'], int)
    assert len(list(patient.models)) > 0
    assert len(list(patient.models)) == patient['pipeline_length']

    # assert defaults are present
    for mid, model in enumerate(patient.models):
        for required_key in ['event', 'event_id']:
            assert required_key in model
        assert model == patient.get_model(mid)
        assert patient.event(mid) == model['event']
        assert patient.event_id(mid) == model['event_id']

    assert patient.event(-1) == ''
    assert patient.event_id(-1) == 0
    assert patient.event_from_id(0) == patient.event(0)
    assert patient.event_from_id(0) == patient.event(1)
    assert patient.event_from_id(0) != patient.event(5)


def test_patient_events_equal(tmp_path):
    patient = Patient(tmp_path)
    ref = patient.set_models()
    assert ref == patient # returns ref of itself
    for mid, model in enumerate(patient.models):
        assert model == patient.get_model(mid)

def test_patient_not_overwrite_existing_events(tmp_path):
    # it shoult not be OK for valid values
    patient = Patient(tmp_path)
    events = [{'event': 't', 'models': [{'test': 'a'}]}]
    patient['events'] = events
    with pytest.raises(AssertionError):
        patient.set_models()

    # but it should be fine with overwrite
    patient.set_models(overwrite=True)

def test_convert_config_yaml_to_xml(tmp_path):
    """Weakly test the conversion of YAML format towards XML."""

    # create xml document
    config = Patient(tmp_path).set_defaults(0, 1).set_models()
    config_xml = dict_to_xml(config)

    # check basic items
    assert config_xml.tag == 'virtualPatient'

    # check patient
    vp = config_xml.findall('Patient')
    assert vp is not None
    assert len(vp) == 1

    # check some contents of the <Patient>
    vp = vp[0]
    for k in ['id', 'random_seed', 'HeartRate']:
        element = vp.findall(k)
        assert element is not None
        assert len(element) == 1

def test_patient_status_string(tmp_path):
    patient = Patient(tmp_path)
    patient.set_models()

    status = patient.status()
    assert len(status.split()) == len(list(patient.models)) + 2 # +2 for the braces

    # only "x" after initialise
    for flag in status.split()[1:-1]:
        assert flag == "x"

    # assert we obtain 'o' for a passed event
    patient['completed'] = 0
    status = patient.status()
    assert status.split()[1] == "o"

    # assert same result for `completed_event`
    patient.set_models(overwrite=True)
    patient.completed_model(0)
    status = patient.status()
    assert status.split()[1] == "o"

def test_patient_is_patient(tmp_path):
    assert Patient.path_is_patient(tmp_path) == False
    patient = Patient(tmp_path).set_models().to_yaml()
    assert Patient.path_is_patient(tmp_path)

def test_patient_completed_event(tmp_path):
    patient = Patient(tmp_path)
    patient.set_models()

    # mark one complete
    patient.completed_model(0)
    assert patient.completed == 0

    # mark all complete
    for mid, _ in enumerate(patient.models):
        patient.completed_model(mid)

    # verify all are complete
    assert patient.completed == len(list(patient.models)) - 1

# example config
document = """
ASPECTS_BL: 8.363497670402376
DiastolePressure: 10100
HeartRate: 60
MeanRightAtrialPressure: 0
NIHSS_BL: 12.808330560011507
StrokeVolume: 70
SystolePressure: 17300
age: 81.38059637671113
collaterals: 1.0
dur_oer: 86.60659896539732
er_iat_groin: 77.00683786676517
events:
- event: baseline
  models:
  - label: bloodflow
  - label: perfusion
    type: PERFUSION
  - label: perfusion
    type: OXYGEN
- event: stroke
  models:
  - label: place_clot
  - label: bloodflow
  - label: perfusion
    type: PERFUSION
  - label: perfusion
    type: OXYGEN
- event: treatment
  models:
  - label: thrombectomy
  - label: bloodflow
  - evaluate_infarct_estimates: true
    label: perfusion
    type: PERFUSION
  - label: perfusion
    type: OXYGEN
  - label: patient_outcome
labels:
  bloodflow: 1d-blood-flow
  patient_outcome: patient-outcome-model
  perfusion: perfusion_and_tissue_damage
  place_clot: place_clot
  thrombectomy: thrombectomy
  thrombolysis: thrombolysis
  tissue_damage: tissue_damage
git_sha: 90745bc25f537cc326958ac7279c865bd0d140bb
id: 0
name: Lucas Jacket
occlsegment_c_short: 2.0
pipeline_length: 12
premrs: 0.0
prev_af: 0.0
prev_dm: 0.0
prev_str: 0.0
random_seed: 577090037
rr_syst: 181.3978800889115
sex: 1.0
sex_long: male
completed: -1
"""

def test_patient_validate_config(tmp_path):
    config = yaml.load(document, yaml.SafeLoader)
    patient = Patient(tmp_path, **config)
    assert patient.validate()

    # without any keys
    patient = Patient(tmp_path)
    assert not patient.validate()

def test_patient_default_clot_file(tmp_path):
    config = yaml.load(document, yaml.SafeLoader)
    patient = Patient(tmp_path, **config)
    assert patient.validate()

    patient.create_default_files()

    clot_file = patient.dir.joinpath("Clots.txt")
    assert os.path.isfile(clot_file)

    with open(clot_file, "r") as clot:
        line = clot.readline().strip()
        for c in line.split(","):
            assert c in ['Vesselname', 'Clotlocation(mm)', 'Clotlength(mm)', 'Permeability', 'Porosity']

        line = clot.readline().strip().split(",")
        assert len(line) == 5

@pytest.mark.parametrize("enum, label", [
    (Model.BLOODFLOW, "1d-blood-flow"),
    (Model.PERFUSION, "perfusion_and_tissue_damage"),
    (Model.PLACE_CLOT, "place_clot"),
    (Model.THROMBECTOMY, "thrombectomy"),
    (Model.THROMBOLYSIS, "thrombolysis"),
    (Model.PATIENT_OUTCOME, "patient-outcome-model"),
    (None, ""),
    (None, "non-existing-event"),
])
def test_event_enum_from_string(enum, label):
    assert Model.from_str(label) == enum
    if enum:
        assert Model.from_name(enum.name) == enum

@pytest.mark.parametrize("enums, labels, valid", [
    ([Model.BLOODFLOW], "1d-blood-flow", True),
    ([Model.BLOODFLOW], ["1d-blood-flow"], True),
    ([Model.BLOODFLOW], ["1d-blood-flow", "non-existing"], False),
    ([Model.BLOODFLOW, Model.PLACE_CLOT], ["1d-blood-flow", "place_clot"], True),
    ([], [], True),
    ([], "", False),
    ([], "non-existing-event", False),
    ([], ["non-existing-event"], False),
])
def test_parse_models(enums, labels, valid):
    events = Model.parse_models(labels)
    for event, enum in zip(events, labels):
        assert event == enum
    assert Model.validate_models(labels) == valid

@pytest.mark.parametrize("enum, label, valid", [
    (Event.BASELINE, "baseline", True),
    (Event.STROKE, "stroke", True),
    (Event.TREATMENT, "treatment", True),
    (None, "", False),
    (None, "non-existing-state", False),
])
def test_state_enum_from_string(enum, label, valid):
    assert Event.from_str(label) == enum
    assert Event.validate_event(label) == valid

@pytest.mark.parametrize("enum, label, valid", [
    (Event.BASELINE, 0, True),
    (Event.STROKE, 1, True),
    (Event.TREATMENT, 2, True),
])
def test_state_enum_from_index(enum, label, valid):
    assert Event(label) == enum
    assert Event.validate_event(label) == valid

def test_terminate(tmp_path):
    p = Patient(tmp_path)
    assert not p.terminated

    p.terminate()
    assert p.terminated

    for b in [True, False]:
        p.terminated = b
        assert p.terminated == b

def test_patient_reset(tmp_path):
    p = Patient(tmp_path)
    assert not p.terminated

    p.terminate()
    assert p.terminated

    p.reset()
    assert not p.terminated

def test_patients_from_trial(trial_directory):
    trial = pathlib.Path(trial_directory)
    patient = trial.joinpath('patient')

    # create tmp dirs
    for p in [trial, patient]:
        os.makedirs(p, exist_ok=True)

    # create a patient and another file
    p = Patient(patient).to_yaml()
    other = trial.joinpath('other.txt').touch()

    # assert only one patient is found, and equal to what was generated
    assert len(list(patients_from_trial(trial))) == 1
    assert list(patients_from_trial(trial))[0] == p
