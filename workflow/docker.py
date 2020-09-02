import os
import pathlib
import subprocess
import logging

from workflow.container import Container, ContainerType
import workflow.utilities as utilities


class Docker(Container):
    def __init__(self):
        super().__init__()
        self.type = ContainerType.DOCKER

        # Docker requires the use of `sudo` for each command on Linux. Any
        # other environment does not require this, as they run inside another
        # VM
        self.sudo = 'sudo' if self.os == utilities.OS.LINUX else ''

        # Docker uses the `-v [path_1:path_2]` argument to indicate that the
        # following paths represent the host's path (path_1) and the local
        # path (path_2) inside the container. Multiple volumes to bind are
        # allowed as long as these are prefixed by the `bind_flag` `-v`.
        self.bind_flag = '-v '

    def image(self, path):
        """Return the image's tag as defined by the basename of the path."""
        # The `isct` command builds all Docker containers where the tags are
        # matched to the basename of the directories. Therefore, we only need
        # to split the basename here to obtain the corresponding image tag.
        return os.path.basename(pathlib.Path(path))

    def build_image(self, path):
        """Build the Docker image of the Dockerfile in `path`."""
        # FIXME: introduce a check that Dockerfile is found?

        # Docker can build from anywhere, when given an absolute path.
        path = pathlib.Path(path).absolute()
        tag = self.image(path)
        return f"{self.sudo} {self.type} build {path} -t {tag}".split()

    def check_image(self, path):
        """Returns a command to test container with tag `path` exists."""
        tag = self.image(path)
        return f"{self.sudo} {self.type} image inspect {tag}".split()

    def set_permissions(self, path, dry_run=True):
        """Updates the file permissions after Docker runs to prevent files
        remaining on the filesystem with `root` permissions inherited from the
        Docker container."""
        if self.os == utilities.OS.LINUX:
            user = subprocess.check_output(['whoami'],
                                           universal_newlines=True).strip()
            chown = ["sudo", "chown", "-R", f"{user}:{user}", str(path)]

            # log the command
            logging.info(" + " + " ".join(chown))

            # only evaluate when not doing a dry run
            if not dry_run:
                subprocess.run(chown)
