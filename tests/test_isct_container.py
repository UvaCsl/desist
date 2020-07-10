import docopt
import pytest
import schema
import os

from workflow.isct_container import container
from tests.test_isct_trial import trial_directory

@pytest.mark.parametrize("arg", ([1, 1.0, "/novalidpath", None]))
def test_container_invalid_arguments(arg):
    with pytest.raises(SystemExit):
        if arg is None:
            container("")
        else:
            container(f"container build {arg}".split())

@pytest.mark.parametrize("arg", (["", "-v", "-x", "-vx"]))
def test_container_valid_path(trial_directory, arg):
    path = trial_directory.absolute()
    os.mkdir(path.absolute())

    assert os.path.isdir(path.absolute())
    container(f"container build {path} {arg}".split())

    paths = " ".join([str(path) for i in range(10)])
    container(f"container build {paths} {arg}".split())

