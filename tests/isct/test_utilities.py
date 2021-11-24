import os
import pathlib
import pytest

from desist.isct.utilities import OS, MAX_FILE_SIZE
from desist.isct.utilities import CleanFiles, FileCleaner
from desist.isct.utilities import is_bind_path
from desist.isct.utilities import extract_simulation_times
from desist.isct.events import Event, Events
from desist.isct.config import Config


baseline_event = Event({
    'event':
    'baseline',
    'models': [{
        'label': '1d-blood-flow',
    }, {
        'label': 'perfusion_and_tissue_damage',
        'type': 'PERFUSION'
    }]
})

stroke_event = Event({
    'event':
    'stroke',
    'models': [{
        'label': 'place_clot',
    }, {
        'label': '1d-blood-flow',
    }, {
        'label': 'perfusion_and_tissue_damage',
        'type': 'PERFUSION'
    }]
})

treatment_event = Event({
    'event':
    'treatment',
    'models': [{
        'label': 'simple-thrombolysis',
    }, {
        'label': 'thrombectomy',
    }, {
        'label': '1d-blood-flow',
    }, {
        'evaluate_infarct_estimates': True,
        'label': 'perfusion_and_tissue_damage',
        'type': 'PERFUSION'
    }, {
        'label': 'perfusion_and_tissue_damage',
        'type': 'TISSUE-HEALTH'
    }, {
        'label': 'patient-outcome-model'
    }]
})

default_events = Events([baseline_event, stroke_event, treatment_event])
default_labels = {k: k.replace("_", "-") for k in default_events.labels}
default_config = {'events': default_events.to_dict(), 'labels': default_labels}


def default_criteria_file(path):
    config_path = pathlib.Path(path).joinpath('config.yml')
    config = Config(config_path, default_config)
    config.write()
    return str(config.path)


def create_dummy_file(path, filesize):
    """Helper routine to create a dummy file with desired size."""
    with open(path, "wb") as outfile:
        outfile.seek(filesize - 1)
        outfile.write(b"\0")
    return path


@pytest.mark.parametrize("string, platform", [("darwin", OS.MACOS),
                                              ("linux", OS.LINUX)])
def test_OS_enum(string, platform):
    assert OS.from_platform(string) == platform

    with pytest.raises(SystemExit):
        OS.from_platform("windows")


def test_file_cleaner_initialisation():
    with pytest.raises(AssertionError):
        _ = FileCleaner(True)


@pytest.mark.parametrize('mode',
                         [CleanFiles.ALL, CleanFiles.LARGE, CleanFiles.NONE])
@pytest.mark.parametrize('fn, delta, remains', [('removes.txt', +10, False),
                                                ('remains.txt', -10, True),
                                                ('remains.yml', +10, True),
                                                ('remains.yaml', +10, True),
                                                ('config.xml', +10, True),
                                                ('anyother.xml', +10, False)])
def test_file_cleaner_clean_files(tmpdir, mode, fn, delta, remains):
    path = pathlib.Path(tmpdir)
    filename = path.joinpath(fn)
    filesize = MAX_FILE_SIZE + delta

    create_dummy_file(filename, filesize)
    assert filename.exists(), "Test file should be present at start"

    file_cleaner = FileCleaner(mode)
    assert file_cleaner.clean_files(path.joinpath("not/existing")) == (0, 0)
    cnt, size = file_cleaner.clean_files(path)

    if mode == CleanFiles.NONE:
        assert filename.exists(), "Should not be removed."
        assert (cnt, size) == (0, 0), "No removals have happened."
        return

    if mode == CleanFiles.LARGE:
        assert filename.exists() == remains, "File below 1MB threshold."
        expected = (0, 0) if remains else (1, filesize)
        assert (cnt, size) == expected

    if mode == CleanFiles.ALL:
        if not file_cleaner.is_skip_file(filename):
            assert not filename.exists(), "File should be removed."
            assert (cnt, size) == (1, filesize)
        return


@pytest.mark.parametrize('inp,out', [('all', CleanFiles.ALL),
                                     ('1mb', CleanFiles.LARGE),
                                     ('none', CleanFiles.NONE),
                                     (CleanFiles.ALL, CleanFiles.ALL),
                                     (CleanFiles.LARGE, CleanFiles.LARGE),
                                     (CleanFiles.NONE, CleanFiles.NONE)])
def test_clean_files_from_string(inp, out):
    assert CleanFiles.from_string(inp) == out


@pytest.mark.parametrize('path,expected', [('some:other', True),
                                           ('host/path:local/path', True),
                                           ('host/path::local/path', False),
                                           ('host/path', False)])
def test_is_bind_path(tmpdir, path, expected):
    assert is_bind_path(path) == expected
    path = pathlib.Path(tmpdir).joinpath(path)
    os.makedirs(path, exist_ok=True)
    assert not is_bind_path(path), "Should always fail if the file is exists"


timing_test_log = """2021-11-03 07:18:51,274 singularity run
2021-11-03 07:28:16,458 singularity run
2021-11-03 07:28:16,776 singularity run
2021-11-03 07:32:10,684 singularity run
2021-11-03 07:32:12,387 singularity run
2021-11-03 07:36:15,743 singularity run
2021-11-03 07:39:33,346 singularity run
"""


def test_extract_simulation_times(tmpdir):
    logfile = pathlib.Path(tmpdir).joinpath('test.log')
    logfile.write_text(timing_test_log)

    timings = extract_simulation_times(logfile).splitlines()
    assert len(timings) == len(timing_test_log.splitlines())
    assert "2021-11-03 07:18:51" in timings[0] and "Elapsed" in timings[0]
    assert "2021-11-03 07:36:15" in timings[-1] and "0:03:18" in timings[-1]
