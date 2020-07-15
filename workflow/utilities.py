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

def tree(path, prefix="", recurse=False, patient_only=True, report=None):
    """Tree recursively generates a visual tree structure line by line.

    Tree prints the provided path and subsequently exhausts its inner_tree
    routine to provide a line-by-line output of the subdirectories contents.

    Keyword arguments:
    prefix:     A string to be prefixed before every line-by-line output.
    recurse:    If True recurses in all subdirectories of path.
    patient_only:     If True allows to report status of directories that represent
                patients.

    Reference: https://stackoverflow.com/a/59109706
    """

    # show the top directory before recursing into all subdirectories
    print(prefix + f"{os.path.basename(path)}/")
    for line in inner_tree(path, prefix=prefix, recurse=recurse, report=report, patient_only=patient_only):
        print(line)

def inner_tree(path, prefix="", recurse=True, patient_only=True, report=None):
    """Recursive routine of tree. Yields line-by-line output."""

    # prefix components:
    space =  '    '
    branch = '│   '

    # pointers:
    tee =    '├── '
    last =   '└── '

    # contents of the directories, including files
    contents = list(path.iterdir())

    # filter any content that does not equal a patient's directory
    if patient_only:
        contents = list(filter(lambda x: os.path.isdir(x), contents))

    # alfabetical order
    contents.sort()

    # setup the right number of indicators
    pointers = [tee] * (len(contents) - 1) + [last]

    # traverse the content
    for pointer, path in zip(pointers, contents):

        status_str = ""

        # append the status of the patient when reporting
        if path.is_dir() and report is not None:
            status_str += report(path)

        yield prefix + pointer + path.name + status_str

        # recurse into directories if desired
        if path.is_dir() and recurse:
            extension = branch if pointer == tee else space
            yield from inner_tree(path, prefix=prefix+extension, recurse=recurse, patient_only=patient_only, report=report)
