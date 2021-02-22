""":class:`~isct.container.Container` implemementation for ``Singularity``."""
import pathlib

from .container import Container
from .runner import Logger


class Singularity(Container):
    """Implements :class:`~isct.container.Container` for ``Singularity``."""
    def __init__(self, path, container_path, runner=Logger()):
        super().__init__(path, runner=runner)
        self.container_path = pathlib.Path(container_path).absolute()
        self.sudo = 'sudo'
        self.bind_flag = '-B'

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
        """Returns true if the Singularity container image exists."""
        cmd = f'test -e {str(self.container)}'
        return self.runner.run(cmd.split(), check=True)

    def run(self, args=''):
        """Evaluate the Singularity command."""
        cmd = f'singularity run {self.volumes} {self.container} {args}'
        return self.runner.run(cmd.split())
