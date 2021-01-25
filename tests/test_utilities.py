import pytest

from isct.utilities import OS


@pytest.mark.parametrize("string, platform", [("darwin", OS.MACOS),
                                              ("linux", OS.LINUX)])
def test_OS_enum(string, platform):
    assert OS.from_platform(string) == platform

    with pytest.raises(SystemExit):
        OS.from_platform("windows")
