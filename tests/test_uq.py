import pytest
import numpy as np
import os
import pathlib

from isct.patient import Patient

# skip tests when `easyvvuq` is not present
pytest.importorskip("easyvvuq")

# attempt to load modules with requiring extra feature `vvuq`
try:
    from isct.uq import ISCTDecoder
    from easyvvuq.decoders.yaml import YAMLDecoder
except ImportError:
    import warnings
    warnings.warn('depencey `EasyVVUQ` not found: '
                  'please install with feature `vvuq` enabled')
    pass


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
