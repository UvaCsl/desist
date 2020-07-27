import os
import pathlib
import shutil

from workflow.container import Container, ContainerType
import workflow.utilities as utilities

class Singularity(Container):
    def __init__(self, path=None):
        super().__init__()
        self.type = ContainerType.SINGULARITY
        self.bind_flag = '-B '

        self.image_path = "." if path is None else path
        self.image_path = pathlib.Path(self.image_path).absolute()

        assert os.path.isdir(self.image_path), "Singularity path must exist."

    def dry_build(self):

        if self.os == utilities.OS.MACOS:
            # For `MACOS` having the Singularity command present is not
            # sufficient. This only provide means to run the images, whereas
            # building the images requires the additional `vagrant` VM to be
            # present.
            return not self.executable_present() or shutil.which("vagrant") is None

        return not self.executable_present()

    def image(self, path):
        path = self.image_path.joinpath(path)
        return f"{pathlib.Path(path).absolute()}.sif"

    def build_image(self, path):
        """Builds the `image.sif` container image using Singularity."""
        path = pathlib.Path(path)
        base = os.path.basename(path)

        # images are build in the local directory of definition file
        chdir = f"cd {path.absolute()}"
        cmd = f"sudo {self.type} build --force {base}.sif singularity.def"
        mv = f"mv {path}/{base}.sif {self.image_path}/{base}.sif"

        if self.os == utilities.OS.LINUX:
            return f"{chdir} && {cmd} && {mv}".split()

        # On `macos` we require to evaluate the singularity build command inside
        # a `vagrant` VM. This machine shares `/vagrant/` with the directory
        # containing all submodules, therefore `cd` into the path's basename.
        chdir = f"cd /vagrant/{os.path.basename(path)}"

        # `vagrant` accepts singularity commands over ssh and move the resulting
        # image file `singularity.sif` to the desired directory.
        return f'vagrant ssh -c "{chdir} && {cmd}" && {mv}'.split()

    def check_image(self, path):
        """Returns a command to test if the `.sif` file of the path exists."""
        path = self.image(path)
        return f"test -e {path}".split()
