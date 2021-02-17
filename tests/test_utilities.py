import pathlib
import pytest

from isct.utilities import OS, clean_large_files


@pytest.mark.parametrize("string, platform", [("darwin", OS.MACOS),
                                              ("linux", OS.LINUX)])
def test_OS_enum(string, platform):
    assert OS.from_platform(string) == platform

    with pytest.raises(SystemExit):
        OS.from_platform("windows")


def test_remove_large_files(tmpdir):
    path = pathlib.Path(tmpdir)
    names = ['removes.txt', 'remains.txt', 'remains.yml']
    files = [path.joinpath(fn) for fn in names]

    for (fn, delta) in zip(files, [+10, -10, +10]):
        with open(fn, "wb") as outfile:
            outfile.seek(2**20 + delta)
            outfile.write(b"\0")

    assert all(map(lambda p: p.exists(), files))
    assert clean_large_files(path) == (1, 2**20 + 10 + 1)
    assert list(map(lambda p: p.exists(), files)) == [False, True, True]

    assert clean_large_files(path.joinpath("not/existing")) is None
