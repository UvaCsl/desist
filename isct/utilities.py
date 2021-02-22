"""General utility routines for ``isct``."""

import enum
import logging
import os
import pathlib
import sys


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
    skip_suffix = ['.yml', '.xml']

    path = pathlib.Path(path)
    if not path.exists():
        return

    for (parent, subdirs, files) in os.walk(path.absolute()):
        for name in files:
            filename = pathlib.Path(parent).joinpath(name)

            if filename.suffix in skip_suffix:
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
