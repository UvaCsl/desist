import pathlib
import pytest

from desist.isct.utilities import OS, MAX_FILE_SIZE
from desist.isct.utilities import CleanFiles, FileCleaner


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


@pytest.mark.parametrize('inp,out',
                         [('all', CleanFiles.ALL),
                          ('1mb', CleanFiles.LARGE),
                          ('none', CleanFiles.NONE),
                          (CleanFiles.ALL, CleanFiles.ALL),
                          (CleanFiles.LARGE, CleanFiles.LARGE),
                          (CleanFiles.NONE, CleanFiles.NONE)])
def test_clean_files_from_string(inp, out):
    assert CleanFiles.from_string(inp) == out
