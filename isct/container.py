import abc
import os
import pathlib

from .runner import Logger


def create_container(path, container_path=None, runner=Logger()):
    if container_path:
        from .singularity import Singularity
        return Singularity(path, container_path, runner=runner)

    from .docker import Docker
    return Docker(path, runner=runner)


# FIXME: consider making `self.volumes` a `@property` of the class, as the
# routine is the same for `Docker` and `Singularity` except the flags `-v` and
# `-B`.


class Container(abc.ABC):
    """Abstract base class for container environments. """
    def __init__(self, path, runner=Logger()):
        path = pathlib.Path(path)
        parent, base = path.parent, os.path.basename(path)
        self.path = parent.joinpath(base)

        self.hosts = []
        self.locals = []
        self.volumes = []
        self.runner = runner

    def bind(self, host, local):
        """Bind volume from host to local."""
        self.hosts.append(pathlib.Path(host).absolute())
        self.locals.append(pathlib.Path(local))
        self.volumes.append(f'{self.hosts[-1]}:{self.locals[-1]}')

    @abc.abstractmethod
    def run(self, args=''):
        """Run a container."""

    @abc.abstractmethod
    def create(self):
        """Create a container."""

    @abc.abstractmethod
    def exists(self):
        """Image exists?"""
