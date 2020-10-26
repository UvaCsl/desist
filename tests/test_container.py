import os
import pytest
import pathlib

from mock import patch

from workflow.utilities import OS
from workflow.container import new_container, Container
from workflow.docker import Docker
from workflow.singularity import Singularity
from workflow.container import ContainerType

from tests.test_utilities import log_subprocess_run, mock_check_output

@pytest.mark.parametrize("singularity, cls", [(".", Singularity), (None, Docker)])
def test_new_container_instance(singularity, cls):
    c = new_container(singularity)
    assert isinstance(c, cls)

@pytest.mark.parametrize("enum, string", [
        (ContainerType.DOCKER, "docker"),
        (ContainerType.SINGULARITY, "singularity"),
    ])
def test_string_container_type(enum, string):
    assert str(enum) == string

@pytest.mark.parametrize("os_str, os", [("linux", OS.LINUX), ("darwin", OS.MACOS)])
@pytest.mark.parametrize("container_type", [".", None])
def test_container_instance_defaults(os_str, os, container_type, mocker):
    mocker.patch("sys.platform", os_str)
    c = new_container(container_type)
    assert c.os == os
    assert c.volumes == []

@pytest.mark.parametrize("permissions", [False, True])
@pytest.mark.parametrize("os_str, os", [("linux", OS.LINUX), ("darwin", OS.MACOS)])
def test_docker_container_sudo(permissions, os_str, os, mocker):
    mocker.patch("sys.platform", os_str)
    c = Docker(permissions=permissions)
    if os == OS.LINUX:
        if permissions:
            assert c.sudo == ''
        else:
            assert c.sudo == "sudo"
    if os == OS.MACOS:
        assert c.sudo == ''

def test_container_bind_flags():
    c = Docker()
    assert c.bind_flag == "-v "
    c = Singularity()
    assert c.bind_flag == "-B "

@pytest.mark.parametrize("host, local", [
        ("/home/folder", "/patient"),
        ("/home/folder/", "/patient/"),
        (pathlib.Path("/home/folder"), "/patient"),
        (pathlib.Path("/home/folder/"), "/patient/"),
        (pathlib.Path("/home/folder"),  pathlib.Path("/patient")),
        (pathlib.Path("/home/folder/"), pathlib.Path("/patient/")),
    ])
@pytest.mark.parametrize("container_type", [".", None])
def test_container_bind_volume(host, local, container_type):
    c = new_container(container_type)
    assert c.volumes == []

    for i in range(2):
        c.bind_volume(host, local)
        assert len(c.volumes) == i + 1
        assert c.volumes[i] == "/home/folder:/patient"

@pytest.mark.parametrize("container_type", [".", None])
def test_container_detect_executable(container_type, mocker):
    mocker.patch("shutil.which", return_value=None)
    c = new_container(container_type)
    assert c.executable_present() == False
    assert c.dry_run() == True

    mocker.patch("shutil.which", return_value=True)
    assert new_container(container_type).executable_present() == True
    assert c.dry_run() == False

@patch('workflow.container.Container.executable_present', return_value=False)
def test_container_dry_build_with_executable(mock_executable_present, mocker):
    # no executable, all should fail
    for os in [OS.MACOS, OS.LINUX]:
        for c in [Docker(), Singularity()]:
            c.os = os
            assert c.executable_present() == False
            assert c.dry_run() == True
            assert c.dry_build() == c.dry_run()

@patch('workflow.container.Container.executable_present', return_value=True)
def test_container_dry_build_with_executable(mock_executable_present, mocker):
    # now we have an executable, on Linux all should run fine
    for c in [Docker(), Singularity()]:
        c.os = OS.LINUX
        assert c.executable_present() == True
        assert c.dry_run() == False
        assert c.dry_build() == c.dry_run()

    # on mac singularity should fail if vagrant is missing
    c = Singularity()
    c.os = OS.MACOS

    for (vagrant, ref) in zip([None, "/mocker/bin/vagrant"], [True, False]):
        mocker.patch("shutil.which", return_value=vagrant)
        assert c.executable_present() == True
        assert c.dry_run() == False
        assert c.dry_build() == ref

@pytest.mark.parametrize("folder", [
    "", "folder", "folder_with_underscores", "folder-with-dashes"])
@pytest.mark.parametrize("path", [
    "path", "path_with_underscores", "path-with-dashes"])
def test_container_image_format(folder,path):
    p = pathlib.Path(folder).joinpath(path)
    for c in [Docker(), Singularity()]:
        assert os.path.basename(c._format_image(p)) == path.replace("_","-")
        assert c._format_image(p).parent == pathlib.Path(folder)

def test_docker_container_image_tag(tmp_path):
    c = Docker()
    path = c._format_image(pathlib.Path(tmp_path))
    assert  os.path.basename(path) == c.image(tmp_path)

def test_singularity_container_image_tag(tmp_path):
    c = Singularity(tmp_path)
    path = c._format_image(pathlib.Path(tmp_path))
    assert path == c.image(tmp_path)

@pytest.mark.parametrize("os_str, OS", [("linux", OS.LINUX), ("darwin", OS.MACOS)])
def test_docker_check_image_command(os_str, OS, mocker, tmp_path):
    # loosely test if contains the right contents
    mocker.patch("sys.platform", os_str)

    c = Docker()
    cmd = " ".join(c.check_image(tmp_path))

    if OS == OS.LINUX:
        assert "sudo" in cmd

    for k in ['image', 'docker', 'image', 'inspect', os.path.basename(tmp_path)]:
        assert k in cmd

@pytest.mark.parametrize("os_str, OS", [("linux", OS.LINUX), ("darwin", OS.MACOS)])
def test_docker_build_image_command(os_str, OS, mocker, tmp_path):
    # loosely test if contains the right contents
    mocker.patch("sys.platform", os_str)

    c = Docker()
    cmd = " ".join(c.build_image(tmp_path))

    if OS == OS.LINUX:
        assert "sudo" in cmd

    for k in ['build', 'docker', '-t', os.path.basename(tmp_path)]:
        assert k in cmd

@pytest.mark.parametrize("os_str, OS", [("linux", OS.LINUX), ("darwin", OS.MACOS)])
def test_docker_run_image_command(os_str, OS, mocker, tmp_path):
    # loosely test if contains the right contents
    mocker.patch("sys.platform", os_str)

    c = Docker()
    c.bind_volume("host", "local")

    arg = 'my args'
    cmd = " ".join(c.run_image(tmp_path, arg))

    if OS == OS.LINUX:
        assert "sudo" in cmd

    for k in ['run', 'docker', 'host', 'local', ':', c.bind_flag, os.path.basename(c._format_image(pathlib.Path(tmp_path))), arg]:
        assert k in cmd

def test_create_singularity_container_invalid_path(tmp_path):
    with pytest.raises(AssertionError):
        c = Singularity(tmp_path.joinpath("not_existing"))

@pytest.mark.parametrize("os_str, OS", [("linux", OS.LINUX), ("darwin", OS.MACOS)])
def test_singularity_check_image_command(os_str, OS, mocker, tmp_path):
    # loosely test if contains the right contents
    mocker.patch("sys.platform", os_str)

    c = Singularity(tmp_path)
    cmd = " ".join(c.check_image(tmp_path))

    for k in ['test', '-e', os.path.basename(tmp_path)]:
        assert k in cmd

@pytest.mark.parametrize("os_str, OS", [("linux", OS.LINUX), ("darwin", OS.MACOS)])
def test_singularity_build_image_command(os_str, OS, mocker, tmp_path):
    # loosely test if contains the right contents
    mocker.patch("sys.platform", os_str)

    c = Singularity(tmp_path)
    cmd = " ".join(c.build_image(tmp_path))

    if OS == OS.MACOS:
        for k in ['vagrant', 'ssh', '-c']:
            assert k in cmd

    for k in ['cd', 'mv', os.path.basename(tmp_path)]:
        assert k in cmd

@pytest.mark.usefixtures('mock_check_output')
@pytest.mark.usefixtures('log_subprocess_run')
@pytest.mark.parametrize("permissions", [True, False])
@pytest.mark.parametrize("os_str, OS", [("linux", OS.LINUX), ("darwin", OS.MACOS)])
def test_docker_change_permissions(permissions, os_str, OS, mocker, tmp_path):
    path = tmp_path.joinpath("newfile")
    path.touch()

    # set OS
    mocker.patch("sys.platform", os_str)

    # make sure changing permissions does not fail
    for container in [Docker]:
        c = container(permissions)
        cmd = c.set_permissions(path, "tag", dry_run=False)

        if OS == OS.MACOS:
            assert cmd == None
        else:
            # sudo should not be present if permissions are available
            assert (not 'sudo' in cmd) == permissions
            # entrypoint should be present if permissions are given, to overcome
            # the need sudo requirements for chown
            assert ('entrypoint' in cmd) == permissions

