import pathlib
import pytest

from isct.utilities import OS, clean_large_files, MAX_FILE_SIZE


@pytest.mark.parametrize("string, platform", [("darwin", OS.MACOS),
                                              ("linux", OS.LINUX)])
def test_OS_enum(string, platform):
    assert OS.from_platform(string) == platform

    with pytest.raises(SystemExit):
        OS.from_platform("windows")


@pytest.mark.parametrize('fn, delta, remains', [('removes.txt', +10, False),
                                                ('remains.txt', -10, True),
                                                ('remains.yml', +10, True),
                                                ('config.xml', +10, True),
                                                ('anyother.xml', +10, False)])
def test_remove_large_files(tmpdir, fn, delta, remains):
    path = pathlib.Path(tmpdir)
    filename = path.joinpath(fn)
    filesize = MAX_FILE_SIZE + delta

    with open(filename, "wb") as outfile:
        outfile.seek(filesize - 1)
        outfile.write(b"\0")

    assert filename.exists(), "Test file should be present at start"

    cnt, size = clean_large_files(path)
    assert filename.exists() == remains, "Should match desired remain flag"

    if remains:
        assert (cnt, size) == (0, 0), f"'{fn}' should not be removed"
    else:
        assert (cnt, size) == (1, filesize)

    assert clean_large_files(path.joinpath("not/existing")) is None
