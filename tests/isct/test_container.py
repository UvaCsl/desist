import pathlib
import pytest

from desist.isct.container import create_container
from desist.isct.docker import Docker
from desist.isct.singularity import Singularity
from .test_runner import DummyRunner
from desist.isct.utilities import OS


@pytest.mark.parametrize("platform", [OS.MACOS, OS.LINUX])
@pytest.mark.parametrize("path, container_type",
                         [(None, Docker), ("./containers", Singularity)])
def test_new_container(mocker, platform, path, container_type):
    mocker.patch('desist.isct.utilities.OS.from_platform', return_value=platform)
    container = create_container(".", path)
    assert isinstance(container, container_type)


@pytest.mark.parametrize("platform, permission", [(OS.MACOS, ''),
                                                  (OS.LINUX, 'sudo')])
def test_new_container_permission(mocker, platform, permission):
    mocker.patch('desist.isct.utilities.OS.from_platform', return_value=platform)

    # Docker
    container = create_container(".")
    assert container.sudo == permission

    # Singularity
    container = create_container(".", container_path='./container')
    assert container.sudo == 'sudo -E'


@pytest.mark.parametrize("host, local", [
    ("/home/folder", "/patient"),
])
@pytest.mark.parametrize("container", [Docker, Singularity])
def test_bind_volume(container, host, local):
    runner = DummyRunner()
    if container == Docker:
        c = container(".", runner=runner)
        flag = '-v'
    else:
        c = container(".", "./container", runner=runner)
        flag = '-B'

    assert c.volumes == ''
    c.bind(host, local)

    # add host/local pair
    host = pathlib.Path(host).absolute()
    local = pathlib.Path(local)
    assert c.bind_volumes[0] == (host, local)

    # ensure `:` formatting
    assert f'{host}:{local}' in c.volumes

    # run the command; which is traced in the `DummyRunner`s output
    c.run()

    # ensure correct `bind_flag` is present
    assert flag in runner
