import subprocess
import sys

from .container import Container
from .utilities import OS
from .runner import Logger


class Docker(Container):
    """Docker environment."""
    def __init__(self, path, docker_group=False, runner=Logger()):
        super().__init__(path, runner=runner)
        self.docker_group = docker_group
        self.bind_flag = '-v'

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
        cmd = f'{self.sudo} docker run {self.volumes} {self.tag} {args}'
        permissions_cmd = self.update_file_permissions()

        if permissions_cmd is not None:
            cmd = f'{cmd} && {permissions_cmd}'

        return self.runner.run(cmd.split())

    def update_file_permissions(self):
        """Update file permissions for files created within Docker on Linux.

        This routine aims to fix the file permissions for files generated
        within Docker containers, specifically when running on Linux-based
        operating systems on the host machine. The issue arrises from the
        permissions set within the container, as all newly created files have
        root permissions (i.e. the permissions within the Docker environment).

        This creates a problem when the user on the host machine does *not*
        have root permissions as well. In this case, the user is *not* able to
        change the permissions of these newly created files, nor remove them
        from their system.

        This routine considers two scenarios:

        1. The host does have root permissions.
        2. The host does not have root permissions.

        In the first case, we evaluate a `chown` operation to reset the
        permissions from `root:root` back to `user:user`.

        In the second case, we apply some trickery: the Docker container is
        invoked another time to evaluate the `chown` operation where the
        permissions are set to match the original permissions of the volume
        on the host machine.
        """

        if OS.from_platform(sys.platform) != OS.LINUX:
            return None

        # If no volumes were written, no permissions have to be updated
        if len(self.bind_volumes) == 0:
            return None

        if not self.docker_group:

            # convert ownership of the files to ownership of the current user
            user = subprocess.check_output(['whoami']).strip().decode('utf-8')

            # Loop over all volumes that were bound to the container to
            # identify the patient's container, i.e. the path that was
            # explicitly linked to the local `/patient` or `/trial` paths.
            # Docker will write files in this directory with root permissions,
            # which we undo.
            #
            # FIXME: resolve these hardcoded paths
            for (host, local) in self.bind_volumes:
                if '/patient' in str(local) or '/trial' in str(local):
                    permission_path = host
                    break

            return f'sudo chown -R {user}:{user} {str(permission_path)}'

        # In the remaining situation, the user has permissions to run Docker,
        # as the user is part of the "docker group". However, there are no
        # permissions to use `sudo` to reset the file permissions. Thus, to
        # still reset these permissions, well call into the Docker container
        # again specifically to reset these file permissions. Thus, inside the
        # Docker container---with root permissions---we change the ownership
        # of all documents within `/patient/*` to match the ownership of
        # the actual `/patient` directory on the host system.
        #
        # FIXME: it would be much nicer to avoid these operations...
        #
        # Reference discussions at: https://stackoverflow.com/a/29584184
        return (f"docker run --entrypoint /bin/sh {self.volumes}"
                f""" {self.tag} -c """
                f"""chown -R `stat -c "%u:%g" /patient` /patient""")
