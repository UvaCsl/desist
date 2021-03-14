import os
import pathlib
import pytest

from isct.utilities import OS
from isct.singularity import Singularity
from isct.runner import LocalRunner
from test_runner import DummyRunner


@pytest.mark.parametrize("platform", [OS.MACOS, OS.LINUX])
def test_singularity_create(mocker, tmpdir, platform):
    mocker.patch('isct.utilities.OS.from_platform', return_value=platform)

    path = pathlib.Path('tmp')
    container_path = pathlib.Path(tmpdir)

    container = Singularity(path, container_path, runner=DummyRunner())
    result = container.runner.format(container.create())
    cmds = result.split('&&')

    assert len(cmds) == 3

    for key in ['cd', str(path.absolute())]:
        assert key in cmds[0]

    for key in ['sudo', 'singularity', 'build', '--force', 'singularity.def']:
        assert key in cmds[1]

    for key in ['mv', str(path), str(container_path)]:
        assert key in cmds[2]


@pytest.mark.parametrize("platform", [OS.MACOS, OS.LINUX])
def test_singularity_exists(mocker, tmpdir, platform):
    mocker.patch('isct.utilities.OS.from_platform', return_value=platform)

    path = 'tmp'
    container_path = pathlib.Path(tmpdir)
    container = Singularity(path, container_path, runner=DummyRunner())
    result = container.runner.format(container.exists())

    for key in ['test', '-e', f'{container_path}/{path}.sif']:
        assert key in result

    # file not present
    container = Singularity(path, container_path, runner=LocalRunner())
    assert not container.exists()

    # create file, assert presence
    pathlib.Path(f'{container_path}/{path}.sif').touch()
    assert container.exists()


@pytest.mark.parametrize("platform", [OS.MACOS, OS.LINUX])
def test_docker_run(mocker, tmpdir, platform):
    mocker.patch('isct.utilities.OS.from_platform', return_value=platform)

    path = 'tmp'
    container_path = pathlib.Path(tmpdir)
    container = Singularity(path, container_path, runner=DummyRunner())
    result = container.runner.format(container.run(args='args'))

    for key in ['singularity', 'run', os.path.basename(path), 'args']:
        # FIXME: this test is not that robust
        assert key.replace("_", "-") in result
