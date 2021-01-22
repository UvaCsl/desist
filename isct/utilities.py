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
