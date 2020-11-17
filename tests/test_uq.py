import numpy as np
import os
import pathlib
import pytest

from easyvvuq.decoders.yaml import YAMLDecoder
from tests.test_isct_trial import trial_directory
from isct.patient import Patient
from isct.uq import ISCTDecoder


@pytest.mark.parametrize('dat', [{'scalar': 1}, {'vector': [1, 2, 3]}])
def test_yamldecoder_data(tmp_path, dat):
    path = tmp_path
    patient = Patient(path, **dat).to_yaml()
    assert os.path.isfile(patient.path)

    # extract all keys
    decoder = YAMLDecoder(patient.path, list(dat.keys()))

    # point the output parsing to the right directory (normally done by collate)
    data = decoder.parse_sim_output({'run_dir': str(path)})

    # assert all keys
    for k, v in dat.items():
        assert k in data
        assert np.all(data[k] == v)

@pytest.mark.parametrize('dat', [{'scalar': 1}])
def test_isctdecoder(tmp_path, dat):
    path = pathlib.Path(tmp_path)
    patient = Patient(path, **dat).to_yaml()
    assert os.path.isfile(patient.path)

    decoder = ISCTDecoder(patient.path, list(dat.keys()))
    data = decoder.parse_sim_output({'run_dir': str(path)})
    for k, v in dat.items():
        assert k in data
        assert np.all(data[k] == v)
