import pytest
import pathlib
import os
import subprocess
import logging

from mock import patch, MagicMock

from isct.utilities import get_git_hash, isct_module_path, inner_tree, tree
from isct.utilities import OS, run_and_stream, command_succeeds

@pytest.fixture
def log_subprocess_run(mocker):
    mocker.patch('subprocess.run', logging.info)

@pytest.fixture
def mock_check_output(mocker):
    mocker.patch('subprocess.check_output', return_value='string\n')

def test_isct_module_path():
    import isct as wf
    assert isct_module_path().samefile(os.path.split(wf.__file__)[0])

@patch('subprocess.run',
        return_value=subprocess.CompletedProcess(["git", "rev-parse", "HEAD"], returncode=0, stdout="myhash"))
def test_get_git_hash(mock_check_output, tmp_path):
    # output is mocked, we do not know the current hash
    h = get_git_hash(tmp_path)
    assert h == "myhash"

@patch('shutil.which', return_value=None)
def test_git_hash_no_git(mock_which, tmp_path):
    assert get_git_hash(pathlib.Path(tmp_path)) == ""

def test_git_hash_no_git_directory(tmp_path):
    assert get_git_hash(pathlib.Path(tmp_path)) == ""

@pytest.mark.parametrize("report", (lambda n: "", lambda n: "flag"))
@pytest.mark.parametrize("recurse", (True, False))
@pytest.mark.parametrize("dirs", (["one"], ["one", "two"]))
def test_inner_tree(tmp_path, dirs, recurse, report):
    # emtpy directory
    lines = list(inner_tree(tmp_path, recurse=recurse, report=report))
    assert len(lines) == 0

    # setup a nested path
    p = tmp_path
    for folder in dirs:
        p = p.joinpath(folder)
    os.makedirs(p)

    lines = list(inner_tree(tmp_path, recurse=recurse, report=report))

    if recurse:
        assert len(lines) == len(dirs)
        for i, folder in enumerate(dirs):
            assert folder in lines[i]
            assert report("hello") in lines[i]
    else:
        assert len(lines) == 1

    # run through full command and make sure it doesn't crash.
    tree(tmp_path)

def test_OS_enum_values():
    assert OS.LINUX.value == "linux"
    assert OS.MACOS.value == "darwin"

@pytest.mark.parametrize("platform, os", [
        ("linux", OS.LINUX),
        ("linux2", OS.LINUX),
        ("darwin", OS.MACOS),
    ])
def test_OS_enum_init(platform, os):
    assert OS.from_platform(platform) == os

def test_OS_enum_exit_windows():
    # ensure windows fails
    with pytest.raises(SystemExit):
        OS.from_platform("win32")

@pytest.mark.parametrize("cmd, flag", [('true', 0), ('false', 1)])
def test_run_and_stream(cmd, flag):
    assert run_and_stream(cmd, logging) == flag

@pytest.mark.parametrize("cmd, out", [('true', True), ('false', False)])
def test_command_succeeds(cmd, out):
    assert command_succeeds(cmd) == out
    assert command_succeeds(cmd, dry_run=True) == True
