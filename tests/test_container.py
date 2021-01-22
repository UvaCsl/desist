import pytest
import pathlib
import os

from isct.container import Docker, create_container
from test_runner import DummyRunner


def test_new_container():
    assert isinstance(create_container("."), Docker)


@pytest.mark.parametrize("docker_group", [True, False])
def test_docker_exists(docker_group):
    path = 'tmp'
    container = Docker(path, docker_group=docker_group, runner=DummyRunner())
    result = " ".join(container.exists())
    for key in ['docker', 'image', 'inspect', path]:
        assert key in result

    # FIXME: this requires to mock the linux OS
    # assert 'sudo' in result == docker_group


def test_docker_run(tmpdir):
    path = pathlib.Path(tmpdir)
    container = Docker(path, runner=DummyRunner())
    result = ' '.join(container.run(args='args'))
    for key in ['docker', 'run', os.path.basename(path), 'args']:
        # FIXME: this test is not that robust
        assert key.replace("_", "-") in result


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
