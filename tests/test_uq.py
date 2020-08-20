import pytest
import os
import numpy as np
from easyvvuq.decoders.yaml import YAMLDecoder

from workflow.patient import Patient
from tests.test_isct_trial import trial_directory


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
