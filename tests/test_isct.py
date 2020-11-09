import pytest

from isct.isct import main, load_module
from isct.isct_trial import trial as trial_cmd
from isct.isct_patient import patient as patient_cmd
from isct.isct_container import container as container_cmd

import docopt

@pytest.mark.parametrize("cmd", [("--non-sense")])
def test_isct_invalid_arguments(cmd):
    with pytest.raises(docopt.DocoptExit) as e_info:
        main([f"{cmd}"])

def test_isct_invalid_log_path():
    with pytest.raises(SystemExit):
        main(f"--log /non/log.file patient help".split())

def test_isct_no_args():
    with pytest.raises(SystemExit) as e_info:
        main([])

@pytest.mark.parametrize("cmd",
        [
            ("--version"),
            ("''"),
            ("help trial"),
            ("help"),
            ("trial"),
            ("patient"),
            ("container"),
            ("not_existing_cmd"),
            ("help not_existing_cmd"),
        ])
def test_isct_entry_point(cmd):
    with pytest.raises(SystemExit) as e_info:
        main(cmd.split(" "))

@pytest.mark.parametrize("cmd, func",
        [
            ("patient", patient_cmd),
            ("trial", trial_cmd),
            ("container", container_cmd),
        ])
def test_load_module(cmd, func):
    """Assert we obtain the right command on input."""
    assert load_module(cmd) == func

