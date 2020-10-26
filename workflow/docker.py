import os
import pathlib
import subprocess
import logging

from workflow.container import Container, ContainerType
import workflow.utilities as utilities


class Docker(Container):
    def __init__(self, permissions=False):
        super().__init__()
        self.type = ContainerType.DOCKER

        # indicates the user has root permissions for the docker group
        self.permissions = permissions

        # Docker requires the use of `sudo` for each command on Linux. Any
        # other environment does not require this, as they run inside another
        # VM
        self.sudo = ''
        if not self.permissions and self.os == utilities.OS.LINUX:
            self.sudo = 'sudo'

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

    def set_permissions(self, path, tag, dry_run=True):
        """Updates the file permissions after Docker runs to prevent files
        remaining on the filesystem with `root` permissions inherited from the
        Docker container."""

        if self.os == utilities.OS.LINUX:

            # explicitly convert the ownership of the files to current user
            if not self.permissions:
                user = subprocess.check_output(
                    ['whoami'], universal_newlines=True).strip()
                cmd = f"sudo chown -R {user}:{user} {str(path)}".split()

            # The user has permissions to run docker, but no permissions to
            # invoke sudo. Therefore, we leverage the docker container again to
            # update the ownership of all documents with `/patient/` to match
            # the ownership of the actual `/patient` directory.
            #
            # reference: https://stackoverflow.com/a/29584184
            else:
                volumes = " ".join(
                    map(lambda s: self.bind_flag + s, self.volumes))

                cmd = (f"{self.type} run --entrypoint /bin/sh {volumes}"
                       f""" {self.image(tag)} -c """.split())
                cmd.append("""chown -R `stat -c "%u:%g" /patient` /patient""")

            # log the command
            logging.info(" + " + " ".join(cmd))

            # only evaluate when not doing a dry run
            if not dry_run:
                subprocess.run(cmd)

            return " ".join(cmd)
