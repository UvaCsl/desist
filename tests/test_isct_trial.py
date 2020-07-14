import pytest
import os
import shutil
from importlib import util as importlib_util

from mock import patch

from workflow.isct_trial import trial, create_trial_config

@pytest.fixture()
def trial_directory(tmp_path):
    path = tmp_path.joinpath("trial")
    yield path
    # remove path if was created
    if os.path.isdir(path):
        shutil.rmtree(path)

def test_create_trial_folder(trial_directory):
    path = trial_directory
    trial(f"trial create {path}".split())
    assert os.path.isdir(path)

def test_create_trial_in_existing_folder(trial_directory):
    path = trial_directory
    trial(f"trial create {path}".split())
    assert os.path.isdir(path)

    with pytest.raises(SystemExit):
        trial(f"trial create {path}".split())

    # no error when forced
    trial(f"trial create {path} -f -v".split())

def test_create_trial_configuration(trial_directory):
    path = trial_directory
    trial(f"trial create {path}".split())
    assert os.path.isdir(path)

    yml = path.joinpath("trial.yml")
    assert os.path.isfile(yml)

def test_create_trial_configuration_no_docker(trial_directory, mocker):
    path = trial_directory
    trial(f"trial create {path}".split())
    assert os.path.isdir(path)

    mocker.patch("shutil.which", return_value=None)

    yml = path.joinpath("trial.yml")
    assert os.path.isfile(yml)

def test_trial_add_event_configuration(trial_directory):
    """Ensure create_config provides the expected defaults."""
    path = trial_directory
    number = 1
    prefix = "patient"

    config = create_trial_config(path, prefix, number)

    assert config['number'] == number
    assert config['prefix'] == prefix
    assert config['patients_directory'] == str(path.absolute())
    assert config['preprocessed'] == False

@pytest.mark.parametrize("t_prefix, prefix",
        [
            ("''", "patient"),
            ("patient", "patient"),
            ("virtual", "virtual"),
            ("patient folder", "patient_folder"),
        ])
def test_trial_patient_prefix(trial_directory, t_prefix, prefix):
    path = trial_directory
    trial(f"trial create {path} --prefix".split() + [t_prefix])
    assert os.path.isdir(path)

    yml = path.joinpath("trial.yml")
    assert os.path.isfile(yml)

    import yaml
    with open(yml, "r") as outfile:
        config = yaml.load(outfile, yaml.SafeLoader)

    assert config['number'] == 1
    assert config['prefix'] == prefix
    assert config['patients_directory'] == str(path)
    assert config['preprocessed'] == False

@pytest.mark.parametrize("t_n, n", [("1", 1), ("5", 5), ("", SystemExit)])
def test_trial_number_of_patients(trial_directory, t_n, n):
    path = trial_directory

    if isinstance(n, int):
        # valid arguments produce the right number of directories
        trial(f"trial create {path} -n".split() + [t_n])
        assert os.path.isdir(path)

        dirs = [d[0] for d in os.walk(path)]
        assert len(dirs) == n + 1 # account for current directory
    else:
        # invalid arguments produce `SystemExit`
        with pytest.raises(SystemExit):
            trial(f"trial create {path} -n ".split() + [t_n])


@pytest.mark.skipif(importlib_util.find_spec('graphviz') is None,
        reason="requires `graphviz` and `dot` to be present")
def test_trial_plot(trial_directory, mocker):
    """Assert a `.gv` file is found, eventhough `dot` might not be present."""
    path = trial_directory
    trial(f"trial create {path}".split())
    assert os.path.isdir(path)

    trial(f"trial plot {path}".split())
    assert os.path.isfile(path.joinpath("graph.gv"))

    # test output is present when dot is not there
    os.remove(path.joinpath("graph.gv"))
    assert not os.path.isfile(path.joinpath("graph.gv"))

    mocker.patch("shutil.which", return_value=None)
    trial(f"trial plot {path}".split())
    assert os.path.isfile(path.joinpath("graph.gv"))

@pytest.mark.skipif(importlib_util.find_spec('graphviz') is None or shutil.which("dot") is None,
        reason="requires `graphviz` and `dot` to be present")
def test_trial_plot_pdf_render(trial_directory):
    """Assert a pdf is obtained when `graphviz` and `dot` are present."""
    path = trial_directory
    trial(f"trial create {path}".split())
    assert os.path.isdir(path)

    trial(f"trial plot {path}".split())
    assert os.path.isfile(path.joinpath("graph.gv"))
    assert os.path.isfile(path.joinpath("graph.gv.pdf"))

@pytest.mark.skipif(importlib_util.find_spec('graphviz') is None,
        reason="requires `graphviz` and `dot` to be present")
def test_trail_plot_invalid_directory(trial_directory):
    path = trial_directory
    with pytest.raises(SystemExit):
        trial(f"trial plot {path}".split())

def test_trial_run(trial_directory, mocker):
    path = trial_directory
    trial(f"trial create {path} -n 1".split())

    mocker.patch("shutil.which", return_value="/mocker/bin/docker")

    # just a dry run, mock the docker executable path
    trial(f"trial run {path} -x".split())

def test_trial_run_invalid_path(trial_directory):
    path = trial_directory.joinpath("not_existing")
    with pytest.raises(SystemExit):
        trial(f"trial run {path} -x".split())




