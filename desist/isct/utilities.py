"""General utility routines for ``isct``."""

import enum
import logging
import os
import pathlib
import sys
import yaml


# one megabyte
MAX_FILE_SIZE = 2**20


@enum.unique
class OS(enum.Enum):
    """An enumeration to detect the operating system."""
    LINUX = "linux"
    MACOS = "darwin"
    # FIXME: support Windows environment

    @classmethod
    def from_platform(cls, platform: str):
        """Return a :class:`~isct.utilities.OS` from a file system string."""
        if platform == "darwin":
            return cls.MACOS
        elif platform == "linux" or platform == "linux2":
            return cls.LINUX
        else:
            sys.exit("Windows not yet supported.")


@enum.unique
class CleanFiles(enum.Enum):
    """Enumeration containing available file cleaning modes.

    The modes are used by :class:~`isct.utilities.FileCleaner` to determine
    which files need to be removed.
    """
    NONE = "none"
    LARGE = "1MB"
    ALL = "all"

    @classmethod
    def from_string(cls, clean_type: str):
        """Return a :class:~isct.utilities.CleanFiles` from a string.

        This defaults to ``CleanFiles.NONE`` for any unknown conversion to
        ensure no files are deleted when wrong string indicators are provided.

        NOTE: When passing an instance of the CleanFiles enum itself, the
        received instance is returned and no conversion is attempted.
        """
        if isinstance(clean_type, cls):
            # No conversion needed, clean_type is already an CleanFiles enum.
            return clean_type

        if clean_type.lower() == "all":
            return cls.ALL
        elif clean_type.lower() == "1mb":
            return cls.LARGE
        else:
            return cls.NONE


class FileCleaner(object):
    """Allows to clean files from a path.

    The ``FileCleaner`` helps cleaning files from paths. This allows to set
    different suffices or filenames to skip as well as the desired maximum file
    size threshold.
    """
    def __init__(self, mode: CleanFiles, skip_files=['config.xml'],
                 skip_suffix=['.yml', '.yaml'], max_size=MAX_FILE_SIZE):
        assert isinstance(mode, CleanFiles), \
            f"FileCleaner: `mode` argument should be of type: {CleanFiles}."
        self.mode = mode
        self.skip_files = skip_files
        self.skip_suffix = skip_suffix
        self.max_size = max_size
        self.unit = 2**20  # one megabyte

    def is_skip_file(self, path):
        """Returns true on matching skipped filenames or skipped suffices."""
        return path.name in self.skip_files or path.suffix in self.skip_suffix

    def clean_files(self, path):
        """Removes any files larger than 1MB.

        The routine recursively walks all files in the provided directory.
        Anyfile that is larger than `MAX_FILE_SIZE` is deleted.

        Files with suffix either `.yml` or `.xml` are skipped, i.e. the will
        not be deleted, even when their size is above the max size threshold.
        """
        removed_file_count = saved_bytes = 0

        if self.mode == CleanFiles.NONE:
            return removed_file_count, saved_bytes

        path = pathlib.Path(path)
        if not path.exists():
            return removed_file_count, saved_bytes

        for (parent, subdirs, files) in os.walk(path.absolute()):
            for name in files:
                filename = pathlib.Path(parent).joinpath(name)

                if self.is_skip_file(filename):
                    continue

                filesize = filename.stat().st_size
                if self.mode == CleanFiles.ALL or filesize > self.max_size:
                    os.remove(filename)
                    saved_bytes += filesize
                    removed_file_count += 1

        logging.info(
            f"Removed {removed_file_count} files > {self.max_size/self.unit}"
            f"Saved {saved_bytes//self.unit}MB."
        )
        return removed_file_count, saved_bytes


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
