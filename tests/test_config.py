import os
import pathlib
import pytest

from isct.config import Config


@pytest.mark.parametrize('testdict', [{}, {'path': '.'}])
def test_create_config(testdict):
    assert dict(Config('.', testdict)) == testdict


@pytest.mark.parametrize('testdict', [{}, {'path': '.'}])
def test_read_write_config(tmpdir, testdict):
    path = pathlib.Path(tmpdir).joinpath('config.yml')
    config = Config(path, testdict)
    assert dict(config) == testdict

    config.write()
    assert os.path.isfile(config)
    result = Config.read(path)
    assert result == testdict
    for k, v in result.items():
        assert testdict.get(k) == v


def test_read_config_exists(tmpdir):
    with pytest.raises(SystemExit):
        Config.read(tmpdir)

    with pytest.raises(SystemExit):
        Config.read(pathlib.Path(tmpdir).joinpath('file.yml'))
