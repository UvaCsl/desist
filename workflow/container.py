import abc
import enum
import os
import pathlib
import shutil
import sys

import workflow.utilities as utilities


def new_container(singularity_path=None, permissions=False):
    """Generates a specific container instance based on input arguments."""
    if singularity_path is not None:
        from workflow.singularity import Singularity
        return Singularity(singularity_path)
    else:
        from workflow.docker import Docker
        return Docker(permissions=permissions)


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
        # For Docker to execute it only requires that we can find the
        # executable on the current path. Note, on MACOS it might be that the
        # Docker's VM (`docker-machine`) is not accessible, which provides
        # another error. This is not validated in here, as it is directly
        # logged to `stdout`.
        return not self.executable_present()

    def dry_build(self):
        """Return True if system lacks requirements to construct images."""
        return not self.executable_present()

    def _format_image(self, image):
        """Return formatted version of the image.

        All underscores (`_`) are replaced by dashed (`-`) for consistency in
        the container names.
        """
        parent, base = image.parent, os.path.basename(image)
        return parent.joinpath(base.replace("_", "-"))

    @abc.abstractmethod
    def image(self, path):
        """Returns the representation of the image for the specic container."""

    @abc.abstractmethod
    def build_image(self, image):
        """Returns the command as list of strings that builds the image."""

    @abc.abstractmethod
    def check_image(self, path):
        """Returns a command to identify if the container image exists."""

    @abc.abstractmethod
    def image_exists(self, tag, dry_run=True):
        """Returns True if container's image of `tag` exists."""

    @abc.abstractmethod
    def set_permissions(self, path, tag, dry_run=True):
        """Sets the file permissions for the patient directory."""

    def run_image(self, tag, args):
        """Returns the command to run the image corresponding to `tag` where
        the additional arguments `args` are appended to the command."""

        # extract the image corresponding to the tag
        image = self.image(tag)

        # construct the list of volumes to be bound to the container
        volumes = " ".join(map(lambda s: self.bind_flag + s, self.volumes))

        # define the run-command by combining the arguments
        return f"{self.sudo} {self.type} run {volumes} {image} {args}".split()
