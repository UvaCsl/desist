import abc
import enum
import shutil
import pathlib
import sys
import os

import workflow.utilities as utilities

def new_container(singularity_path=None):
    """Generates a specific container instance based on input arguments."""
    if singularity_path is not None:
        from workflow.singularity import Singularity
        return Singularity(singularity_path)
    else:
        from workflow.docker import Docker
        return Docker()

@enum.unique
class ContainerType(enum.Enum):
    DOCKER = "docker"
    SINGULARITY = "singularity"

    def __str__(self):
        return str(self.value)

class Container(abc.ABC):
    def __init__(self):
        self.type = None
        self.volumes = []
        self.os = utilities.OS.from_platform(sys.platform)
        self.sudo = ''

    def bind_volume(self, host, local):
        """Binds a volume to the current container"""
        host = pathlib.Path(host).absolute()
        local = pathlib.Path(local)
        self.volumes += [f"{host}:{local}"]

    def executable_present(self):
        """Returns true if exectuable is present on the system."""
        return shutil.which(str(self.type)) is not None

    def dry_run(self):
        """Returns True if system lacks requirements to execute commands."""
        # For Docker to execute it only requires that we can find the executable
        # on the current path. Note, on MACOS it might be that the Docker's VM
        # (`docker-machine`) is not accessible, which provides another error.
        # This is not validated in here, as it is directly logged to `stdout`.
        return not self.executable_present()

    def dry_build(self):
        """Return True if system lacks requirements to construct images."""
        return not self.executable_present()

    @abc.abstractmethod
    def image(self, path):
        """Returns the representation of the image for the specic container."""
        pass

    @abc.abstractmethod
    def build_image(self, image):
        """Returns the command as list of strings that builds the image."""
        pass

    @abc.abstractmethod
    def check_image(self, path):
        """Returns the command to verify the image exists on the host."""
        pass

    def run_image(self, tag, args):
        """Returns the command to run the image corresponding to `tag` where
        the additional arguments `args` are appended to the command."""

        # extract the image corresponding to the tag
        image = self.image(tag)

        # construct the list of volumes to be bound to the container
        volumes = " ".join(map(lambda s: self.bind_flag + s, self.volumes))

        # define the run-command by combining the arguments
        return f"{self.sudo} {self.type} run {volumes} {image} {args}".split()

