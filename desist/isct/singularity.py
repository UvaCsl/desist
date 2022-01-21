""":class:`~isct.container.Container` implemementation for ``Singularity``."""
import os
import pathlib

from .container import Container
from .runner import Logger


class Singularity(Container):
    """Implements :class:`~isct.container.Container` for ``Singularity``."""
    def __init__(self, path, container_path, runner=Logger()):
        super().__init__(path, runner=runner)
        self.container_path = pathlib.Path(container_path).absolute()
        self.sudo = 'sudo -E'
        self.bind_flag = '-B'

        self.container = self.container_path.joinpath(f'{self.tag}.sif')

    def create(self):
        """Create singularity command.

        Consists of three steps: change directory, create container, and move
        container to the desired container directory at `self.container_path`.
        """
        chdir = f'cd {self.path.absolute()}'
        cmd = f'singularity build --force {self.tag}.sif singularity.def'
        mv = f'mv {self.tag}.sif {self.container_path}/'

        # compose the create command
        cmd = f'{chdir} && sudo -E {cmd} && {mv}'

        # to run multiple commands in the runner, `shell=True` is required
        return self.runner.run(cmd, check=True, shell=True)

    def exists(self):
        """Returns true if the Singularity container image exists."""
        cmd = f'test -e {str(self.container)}'
        return self.runner.run(cmd.split(), check=True)

    def run(self, args=''):
        """Evaluate the Singularity command.

        All containers are evaluated with the ``--containall`` flag to ensure
        reproducibility when running on a wide range of systems. By default
        Singularity will mount the user's home directory and imports the
        available environment variables. As these directories and environment
        settings might have influence on the containers output, and possibly
        have influence on each other when containers are running in parallel,
        it is important to pass ``containall``.

        From the Singularity documentation: "use minimal ``/dev`` and empty
        other directories (e.g. ``/tmp`` and ``$HOME) instead of sharing
        filesytems from your host."

        On some systems running with ``containall`` might be problematic, for
        instance due to too little temporary storage available. The flag can be
        disabled by setting ``SINGULARITY_CONTAINALL=0`` in the running
        environment, which will disable the ``containall`` flag.

        For example, the variable can be set for a single invocation as:

        >>> SINGULARITY_CONTAINALL=0 desist patient run ...
        """

        flags = '--containall'
        if int(os.environ.get("SINGULARITY_CONTAINALL", -1)) == 0:
            flags = ''

        cmd = f'singularity run {flags} {self.volumes} {self.container} {args}'
        return self.runner.run(cmd.split(), check=True)
