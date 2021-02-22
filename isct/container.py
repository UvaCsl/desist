"""The base class representing a virtualised container environment."""

import abc
import os
import pathlib

from .runner import Logger


def create_container(path, container_path=None, runner=Logger()):
    """Returns a specific, initialised container class.

    Args:
        path: The directory of the container on the file system.
        container_path: The directory where to store the resulting container.
        runner: The runner to evaluate the commands.
    """
    if container_path:
        from .singularity import Singularity
        return Singularity(path, container_path, runner=runner)

    from .docker import Docker
    return Docker(path, runner=runner)


class Container(abc.ABC):
    """Abstract base class for container environments."""
    def __init__(self, path, runner=Logger()):
        path = pathlib.Path(path)
        parent, base = path.parent, os.path.basename(path)
        self.path = parent.joinpath(base)
        self.tag = os.path.basename(self.path).replace("_", "-")

        self.bind_volumes = []
        self.bind_flag: str = NotImplemented

        self.runner = runner

    def bind(self, host, local):
        """Add a `(host, local)` path pair to the bind volumes.

        The absolute host path is paired with the local path and appended to
        the list of already appended `(host, local)` pairs.
        """
        host = pathlib.Path(host).absolute()
        local = pathlib.Path(local)
        self.bind_volumes.append((host, local))

    @property
    def volumes(self):
        """Return an argument list of the bind volumes.

        The volumes are typically attached with an specific option flag, e.g.
        `-v` or `-B` for Docker or Singularity. These are variadic arguments,
        that can be repeated any number of times to add multiple pairs of
        `host` to `local` path pairs.
        """
        if len(self.bind_volumes) == 0:
            return ''

        pairs = [f'{host}:{local}' for (host, local) in self.bind_volumes]
        return ' '.join(map(lambda s: f'{self.bind_flag} {s}', pairs))

    @abc.abstractmethod
    def run(self, args=''):
        """Run a container."""

    @abc.abstractmethod
    def create(self):
        """Create a container."""

    @abc.abstractmethod
    def exists(self):
        """Image exists?"""
