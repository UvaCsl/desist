import pathlib
import os

from .container import Container
from .runner import Logger


class Singularity(Container):
    def __init__(self, path, container_path, runner=Logger()):
        super().__init__(path, runner=runner)
        self.container_path = pathlib.Path(container_path).absolute()
        self.tag = os.path.basename(self.path).replace("_", "-")
        self.sudo = 'sudo'

        self.container = self.container_path.joinpath(f'{self.tag}.sif')

    def create(self):
        """Create singularity command.

        Consists of three steps: change directory, create container, and move
        container to the desired container directory at `self.container_path`.
        """

        chdir = f'cd {self.path.absolute()}'
        cmd = f'sudo singularity build --force {self.tag}.sif singularity.def'
        mv = f'mv {self.tag}.sif {self.container_path}/'

        # compose the create command
        cmd = f'{chdir} && {cmd} && {mv}'

        # to run multiple commands in the runner, `shell=True` is required
        return self.runner.run(cmd, check=True, shell=True)

    def exists(self):
        cmd = f'test -e {str(self.container)}'
        return self.runner.run(cmd.split(), check=True)

    def run(self, args=''):
        volumes = ' '.join(map(lambda s: f'-B {s}', self.volumes))
        cmd = f'singularity run {volumes} {self.container} {args}'
        return self.runner.run(cmd.split())
