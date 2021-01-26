import pytest

from isct.container import create_container
from isct.docker import Docker
from isct.singularity import Singularity
from test_runner import DummyRunner
from isct.utilities import OS


@pytest.mark.parametrize("platform", [OS.MACOS, OS.LINUX])
@pytest.mark.parametrize("path, container_type",
                         [(None, Docker), ("./containers", Singularity)])
def test_new_container(mocker, platform, path, container_type):
    mocker.patch('isct.utilities.OS.from_platform', return_value=platform)
    container = create_container(".", path)
    assert isinstance(container, container_type)


@pytest.mark.parametrize("platform, permission", [(OS.MACOS, ''),
                                                  (OS.LINUX, 'sudo')])
def test_new_container_permission(mocker, platform, permission):
    mocker.patch('isct.utilities.OS.from_platform', return_value=platform)

    # Docker
    container = create_container(".")
    assert container.sudo == permission

    # Singularity
    container = create_container(".", container_path='./container')
    assert container.sudo == 'sudo'


@pytest.mark.parametrize("host, local", [
    ("/home/folder", "/patient"),
])
@pytest.mark.parametrize("container", [Docker, Singularity])
def test_bind_volume(container, host, local):
    if container == Docker:
        c = container(".", runner=DummyRunner())
        flag = '-v'
    else:
        c = container(".", "./container", runner=DummyRunner())
        flag = '-B'

    assert c.volumes == []
    c.bind(host, local)
    assert c.volumes[0] == f'{host}:{local}'
    assert flag in ' '.join(c.run())
