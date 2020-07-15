import pytest
import pathlib
import os

from mock import patch

from workflow.utilities import get_git_hash, isct_module_path

def test_isct_module_path():
    import workflow as wf
    assert isct_module_path().samefile(os.path.split(wf.__file__)[0])

@patch('subprocess.check_output', return_value="myhash")
def test_get_git_hash(mock_check_output, tmp_path):
    # output is mocked, we do not know the current hash
    h = get_git_hash(tmp_path)
    assert h == "myhash"

@patch('shutil.which', return_value=None)
def test_git_hash_no_git(mock_which, tmp_path):
    assert get_git_hash(pathlib.Path(tmp_path)) == ""

def test_git_hash_no_git_directory(tmp_path):
    assert get_git_hash(pathlib.Path(tmp_path)) == ""

