import os
import pathlib
import shutil

from workflow.container import Container, ContainerType
import workflow.utilities as utilities

class Singularity(Container):
    def __init__(self):
        super().__init__()
        self.type = ContainerType.SINGULARITY
        self.bind_flag = '-b '

    def dry_build(self):

        if self.os == utilities.OS.MACOS:
            # For `MACOS` having the Singularity command present is not
            # sufficient. This only provide means to run the images, whereas
            # building the images requires the additional `vagrant` VM to be
            # present.
            return not self.executable_present() or shutil.which("vagrant") is None

        return not self.executable_present()

    def image(self, path):
        assert False, "not implemented"

    def build_image(self, path):
        """Builds the `image.sif` container image using Singularity."""
        path = pathlib.Path(path)
        base = os.path.basename(path)

        # images are build in the local directory of definition file
        chdir = f"cd {path.absolute()}"
        cmd = f"sudo {self.type} build --force {base}.sif {base}.def"

        if self.os == utilities.OS.LINUX:
            return f"{chdir} && {cmd}".split()

        # On `macos` we require to evaluate the singularity build command inside
        # a `vagrant` VM. This machine shares `/vagrant/` with the directory
        # containing all submodules, therefore `cd` into the path's basename.
        chdir = f"cd /vagrant/{os.path.basename(path)}"

        # `vagrant` accepts singularity commands over ssh
        return ["vagrant", "ssh", "-c", " ".join(f"{chdir} && {cmd}".split())]

    def image_exist(self, path):
        assert False, "not implemented"

    def run_image(self, path, patient, event_id):
        assert False, "not implemented"

    def check_image(self, path):
        assert False, "not implemented"
