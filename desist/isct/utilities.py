"""General utility routines for ``isct``."""

import enum
import logging
import os
import pathlib
import sys
import yaml


# FIXME: support Windows environment

# one megabyte
MAX_FILE_SIZE = 2**20


@enum.unique
class OS(enum.Enum):
    """An enumeration to detect the operating system."""
    LINUX = "linux"
    MACOS = "darwin"

    @classmethod
    def from_platform(cls, platform: str):
        """Return a :class:`~isct.utilities.OS` from a file system string."""
        if platform == "darwin":
            return cls.MACOS
        elif platform == "linux" or platform == "linux2":
            return cls.LINUX
        else:
            sys.exit("Windows not yet supported.")


def clean_large_files(path):
    """Removes any files larger than 1MB.

    The routine recursively walks all files in the provided directory. Anyfile
    that is larger than `MAX_FILE_SIZE` is deleted.

    Files with suffix either `.yml` or `.xml` are skipped, i.e. the will not
    be deleted, even when their size is above the max size threshold.
    """
    cnt = saved = 0
    skip_suffix = ['.yml']
    skip_files = ['config.xml']

    path = pathlib.Path(path)
    if not path.exists():
        return

    for (parent, subdirs, files) in os.walk(path.absolute()):
        for name in files:

            filename = pathlib.Path(parent).joinpath(name)
            if name in skip_files or filename.suffix in skip_suffix:
                continue

            if (filesize := filename.stat().st_size) > MAX_FILE_SIZE:
                os.remove(filename)
                saved += filesize
                cnt += 1

    # report save file size in MBs
    unit = 1e6
    logging.info(f"Removed {cnt} files large than {MAX_FILE_SIZE//unit}MB. \n"
                 f"Saved {saved//unit}MB.")

    return cnt, saved


def read_yaml(path):
    """Reads the contents from the YAML file at the specified path.

    The routine uses the ``yaml.safe_load`` function, and therefore will only
    read standard YAML tags and cannot handle loading arbitrary Python objects.

    Raises ``IsDirectoryError`` and ``FileNotFoundError`` in case the path or
    file are not encountered on the file system. For any other error the
    function panics, as typically reading the YAML files represent and
    important step in a pipeline that _has_ to work.
    """
    path = pathlib.Path(path)
    try:
        with open(path, 'r') as yaml_file:
            contents = yaml.safe_load(yaml_file)
    except IsADirectoryError:
        raise IsADirectoryError(f'The YAML path `{path}` should be a file.')
    except FileNotFoundError:
        raise FileNotFoundError(f'The YAML path `{path}` is not present.')
    except Exception as err:
        sys.exit(f'Loading YAML from `{path}` raised: `{err}`')

    return contents


def write_yaml(path, dictionary):
    """Writes a dictionary to the given path in the YAML format.

    This routine creates the full directory tree corresponding to the
    provided path ``path``. In case the writing to disk fails, no attempt is
    made to remove any created directories. This avoids having to keep track
    which part of the tree is newly added as well as accidentally dropping
    large directory trees.

    The ``yaml.safe_dump`` function is used, which allows dumping of standard
    YAML tags only. So, no arbitrary Python objects can be written using this
    function.
    """

    # Make sure the full tree of the file path exist on the file system,
    # otherwise attempting to write the file will fail.
    basepath, _ = os.path.split(path)
    os.makedirs(basepath, exist_ok=True)

    with open(path, 'w') as config_file:
        yaml.safe_dump(dictionary, config_file)
