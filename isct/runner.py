import abc
import subprocess

# FIXME: add `ParallelRunner`: push the output over `stdout` for `gnu parallel`
# FIXME: rename constructors to `new_runner`?
# FIXME: make `verbose` mean a local runner with output to logger;


def create_runner(verbose):
    if verbose:
        return Logger()
    else:
        return LocalRunner()


class Runner(abc.ABC):
    def __init__(self):
        pass

    @abc.abstractmethod
    def run(self, cmd, check=True):
        """Run command. Report on result if check == True"""


class Logger(Runner):
    """A runner implementation printing the commands to `stdout`."""
    def __init__(self):
        super().__init__()

    def run(self, cmd, check=True):
        """Prints the commands to `stdout`."""
        print(cmd)


# FIXME: add `verbose` argument:
#        insert `cmd` into the logging
#        insert `output` into the logging
class LocalRunner(Runner):
    """A runner evaluating commands on the local machine."""
    def __init__(self):
        super().__init__()

    def run(self, cmd, check=True):
        """Prints the commands to `stdout`."""
        try:
            subprocess.run(cmd, check=check)
        except subprocess.CalledProcessError:
            if check:
                return False
        return True
