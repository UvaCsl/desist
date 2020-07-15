import pathlib
import shutil
import subprocess
import os

def isct_module_path():
    """Retruns the path to the isct module. """
    import workflow as wf
    bn, fn = os.path.split(wf.__file__)
    return pathlib.Path(bn)

def get_git_hash(path):
    """Return the git hash of path.

    This function can be combined with `utilities.isct_module_path` to get the
    git hash of the install package. Note, this is based on the fact that we
    are working with a local, `pip --editable` installed version of the package.
    This is likely break whenever the package is not installed as an editable
    version, as the modules path probably does not point to a location that
    actually contains a copy of the repository. In those cases, we should
    probably resort to storing the package version (ensuring this is equal to
    a certain git tag) rather then storing specific git hashes in this manner.
    """

    if shutil.which("git") is None:
        return ""

    try:
        # with universal_newlines=True returns a string
        label = subprocess.check_output(
                    ["git", "rev-parse", "HEAD"],
                    universal_newlines=True,
                    cwd=path).strip()
    except subprocess.CalledProcessError:
        label = ""

    return label

