import abc
import os
import pathlib
import sys

from .utilities import OS
from .runner import Logger


# FIXME: define `Singularity` container
def create_container(path, runner=Logger()):
    return Docker(path, runner=runner)


class Container(abc.ABC):
    """Abstract base class for container environments. """
    def __init__(self, path, runner=Logger()):
        path = pathlib.Path(path)
        parent, base = path.parent, os.path.basename(path)
        self.path = parent.joinpath(base)

        self.volumes = []
        self.runner = runner

    def bind(self, host, local):
        """Bind volume from host to local."""
        host = pathlib.Path(host).absolute()
        local = pathlib.Path(local)
        self.volumes.append(f'{host}:{local}')

    @abc.abstractmethod
    def run(self, args=''):
        """Run a container."""

    @abc.abstractmethod
    def create(self):
        """Create a container."""

    @abc.abstractmethod
    def exists(self):
        """Image exists?"""


class Docker(Container):
    """Docker environment."""
    def __init__(self, path, docker_group=False, runner=Logger()):
        super().__init__(path, runner=runner)
        # FIXME: make this a general routine on `Container`
        self.tag = os.path.basename(self.path).replace("_", "-")

        # Docker requires `sudo` when no part of user group; only on Linux
        self.sudo = ''
        if not docker_group:
            if OS.from_platform(sys.platform) == OS.LINUX:
                self.sudo = 'sudo'

    def exists(self):
        cmd = f'{self.sudo} docker image inspect {self.tag}'.split()
        return self.runner.run(cmd, check=True)

    def create(self):
        cmd = f'{self.sudo} docker build {self.path.absolute()} -t {self.tag}'
        return self.runner.run(cmd.split())

    def run(self, args=''):
        volumes = ' '.join(map(lambda s: f'-v {s}', self.volumes))
        cmd = f'{self.sudo} docker run {volumes} {self.tag} {args}'
        return self.runner.run(cmd.split())
        # FIXME: fix permissions
