import pytest
import pathlib
import os

from isct.container import Docker, create_container
from test_runner import DummyRunner
from isct.utilities import OS


@pytest.mark.parametrize("platform, permission", [(OS.MACOS, ''),
                                                  (OS.LINUX, 'sudo')])
def test_new_container(mocker, platform, permission):
    mocker.patch('isct.utilities.OS.from_platform', return_value=platform)
    container = create_container(".")
    assert isinstance(container, Docker)
    assert container.sudo == permission


@pytest.mark.parametrize("platform, permission", [(OS.MACOS, ''),
                                                  (OS.LINUX, 'sudo')])
@pytest.mark.parametrize("docker_group", [True, False])
def test_docker_exists(mocker, docker_group, platform, permission):
    mocker.patch('isct.utilities.OS.from_platform', return_value=platform)
    path = 'tmp'
    container = Docker(path, docker_group=docker_group, runner=DummyRunner())
    result = " ".join(container.exists())

    for key in ['docker', 'image', 'inspect', path]:
        assert key in result

    if not docker_group:
        assert container.sudo == permission
        assert permission in result


@pytest.mark.parametrize("platform, permission", [(OS.MACOS, ''),
                                                  (OS.LINUX, 'sudo')])
def test_docker_run(mocker, tmpdir, platform, permission):
    mocker.patch('isct.utilities.OS.from_platform', return_value=platform)
    path = pathlib.Path(tmpdir)
    container = Docker(path, runner=DummyRunner())
    result = ' '.join(container.run(args='args'))
    for key in ['docker', 'run', os.path.basename(path), 'args']:
        # FIXME: this test is not that robust
        assert key.replace("_", "-") in result


def test_docker_fix_permissions(mocker, tmpdir):
    mocker.patch('isct.utilities.OS.from_platform', return_value=OS.LINUX)
    path = pathlib.Path(tmpdir)

    # without docker group access, with root
    container = Docker(path, docker_group=False, runner=DummyRunner())
    container.bind('path/on/host', '/patient')
    result = ' '.join(container.run(args='args'))
    for key in ['sudo', 'docker', 'run', 'chown -R']:
        assert key in result

    # with docker group access, without root
    container = Docker(path, docker_group=True, runner=DummyRunner())
    container.bind('path/on/host', '/patient')
    result = ' '.join(container.run(args='args'))
    for key in ['docker', 'run', '--entrypoint /bin/sh', 'chown -R', 'stat']:
        assert key in result


@pytest.mark.parametrize("host, local", [
    ("/home/folder", "/patient"),
])
@pytest.mark.parametrize("container", [Docker])
def test_bind_volume(container, host, local):
    c = container(".", runner=DummyRunner())
    assert c.volumes == []
    c.bind(host, local)
    assert c.volumes[0] == f'{host}:{local}'
    assert '-v' in ' '.join(c.run())
