import os
import pathlib
import pytest

from desist.isct.config import Config


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
    with pytest.raises(IsADirectoryError):
        Config.read(tmpdir)

    with pytest.raises(FileNotFoundError):
        Config.read(pathlib.Path(tmpdir).joinpath('file.yml'))


@pytest.mark.parametrize('contents', ['yaml', '--yaml'])
def test_read_config_that_contains_no_mapping(tmpdir, contents):
    path = pathlib.Path(tmpdir).joinpath('no-mapping.yml')
    with open(path, 'w') as outfile:
        outfile.write(contents)

    with pytest.raises(AssertionError, match='collections.abc.Mapping'):
        Config.read(path)


@pytest.mark.parametrize('contents', ['*yaml', '{yaml'])
def test_read_wrong_config(tmpdir, contents):
    path = pathlib.Path(tmpdir).joinpath('broken.yml')
    with open(path, 'w') as outfile:
        outfile.write(contents)

    # assert `SystemExit` on reading a faulty `yaml` file, where faulty here
    # simply induces an other error than `IsADirectoryError` or
    # `FileNotFoundError`, which both have explicit except statements
    with pytest.raises(SystemExit, match=f'Loading YAML from `{path}` '):
        Config.read(path)
