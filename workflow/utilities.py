import pathlib
import shutil
import subprocess
import os
import enum
import sys


@enum.unique
class OS(enum.Enum):
    LINUX = "linux"
    MACOS = "darwin"

    @classmethod
    def from_platform(cls, platform):
        if platform == "darwin":
            return cls.MACOS
        elif platform == "linux" or platform == "linux2":
            return cls.LINUX
        else:
            sys.exit("Windows not yet supported.")


def isct_module_path():
    """Retruns the path to the isct module. """
    import workflow as wf
    bn, fn = os.path.split(wf.__file__)
    return pathlib.Path(bn)


def get_git_hash(path):
    """Return the git hash of path.

    This function can be combined with `utilities.isct_module_path` to get the
    git hash of the install package. Note, this is based on the fact that we
    are working with a local, `pip --editable` installed version of the
    package. This is likely break whenever the package is not installed as an
    editable version, as the modules path probably does not point to a location
    that actually contains a copy of the repository. In those cases, we should
    probably resort to storing the package version (ensuring this is equal to a
    certain git tag) rather then storing specific git hashes in this manner.
    """

    if shutil.which("git") is None:
        return ""

    try:
        # with universal_newlines=True returns a string
        label = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            universal_newlines=True,
            cwd=path,
            capture_output=True,
            check=True,
        )
        label = label.stdout.strip()
    except subprocess.CalledProcessError:
        label = ""

    return label


def tree(path, prefix="", recurse=False, dir_filter=None, report=None):
    """Tree recursively generates a visual tree structure line by line.

    Tree prints the provided path and subsequently exhausts its inner_tree
    routine to provide a line-by-line output of the subdirectories contents.

    Keyword arguments:
    prefix:         A string to be prefixed before every line-by-line output.
    recurse:        If True recurses in all subdirectories of path.
    dir_filter:     A function to filter directories. The function should
                    receive a path and return either True/False.
    report:         A function to report additional information on a directory.
                    Any valid path is passed into this function, which is
                    expected to return a string.


    Reference: https://stackoverflow.com/a/59109706
    """

    # show the top directory before recursing into all subdirectories
    print(prefix + f"{os.path.basename(path)}/")
    for line in inner_tree(path,
                           prefix=prefix,
                           recurse=recurse,
                           report=report,
                           dir_filter=dir_filter):
        print(line)


def inner_tree(path, prefix="", recurse=True, dir_filter=None, report=None):
    """Recursive routine of tree. Yields line-by-line output."""

    # prefix components:
    space = '    '
    branch = '│   '

    # pointers:
    tee = '├── '
    last = '└── '

    # contents of the directories, including files
    contents = list(path.iterdir())

    # filter any content on:
    # - being a valid directory (os.path.isdir())
    # - the provided dir_filter argument
    if dir_filter is not None:
        contents = list(filter(lambda x: os.path.isdir(x), contents))
        contents = list(filter(lambda x: dir_filter(x), contents))

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

            yield from inner_tree(path,
                                  prefix=prefix + extension,
                                  recurse=recurse,
                                  dir_filter=dir_filter,
                                  report=report)


def run_and_stream(cmd, logger, shell=False):
    """Run a command with `subprocess.Popen` and stream its output.

    The function returns the returncode of the process.
    """

    logger.info(" + " + " ".join(cmd))

    with subprocess.Popen(cmd,
                          shell=shell,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT,
                          encoding="utf-8",
                          universal_newlines=True) as proc:

        for line in iter(proc.stdout.readline, ''):
            logger.info(f'{line.strip()}\r')

    return proc.returncode
