import os
import pathlib
import pytest

from desist.isct.utilities import OS
from desist.isct.docker import Docker
from test_runner import DummyRunner


@pytest.mark.parametrize("platform, permission", [(OS.MACOS, ''),
                                                  (OS.LINUX, 'sudo')])
@pytest.mark.parametrize("docker_group", [True, False])
def test_docker_create(mocker, platform, permission, docker_group):
    mocker.patch('desist.isct.utilities.OS.from_platform', return_value=platform)

    path = pathlib.Path('tmp')
    container = Docker(path, docker_group=docker_group, runner=DummyRunner())
    result = " ".join(container.create())

    for key in ['docker', 'build', '-t', str(path.absolute())]:
        assert key in result

    if not docker_group:
        assert permission in result


@pytest.mark.parametrize("platform, permission", [(OS.MACOS, ''),
                                                  (OS.LINUX, 'sudo')])
@pytest.mark.parametrize("docker_group", [True, False])
def test_docker_exists(mocker, docker_group, platform, permission):
    mocker.patch('desist.isct.utilities.OS.from_platform', return_value=platform)

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
    mocker.patch('desist.isct.utilities.OS.from_platform', return_value=platform)
    path = pathlib.Path(tmpdir)
    container = Docker(path, runner=DummyRunner())
    result = ' '.join(container.run(args='args'))
    for key in ['docker', 'run', os.path.basename(path), 'args']:
        # FIXME: this test is not that robust
        assert key.replace("_", "-") in result


def test_docker_fix_permissions(mocker, tmpdir):
    mocker.patch('desist.isct.utilities.OS.from_platform', return_value=OS.LINUX)
    path = pathlib.Path(tmpdir)
    host_path = path.joinpath('host')
    os.makedirs(host_path)

    # without docker group access, with root
    runner = DummyRunner()
    container = Docker(path, docker_group=False, runner=runner)
    container.bind(host_path, '/patient')
    result = ' '.join(container.run(args='args'))
    for key in ['sudo', 'docker', 'run', 'chown -R']:
        assert key in runner

    # with docker group access, without root
    runner.clear()
    container = Docker(path, docker_group=True, runner=runner)
    container.bind(host_path, '/patient')
    result = ' '.join(container.run(args='args'))
    stat = os.stat(host_path)

    # assert the right user and group IDs are set
    assert str(stat.st_uid) in result, "Expected user id not found."
    assert str(stat.st_gid) in result, "Expected group id not found."

    for key in ['docker', 'run', '--entrypoint /bin/sh', '-c', 'chown -R']:
        assert key in result
