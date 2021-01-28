import os
import pathlib
import yaml
import sys


"""Summary line.

Extended description of function.
"""


class Config(dict):
    def __init__(self, path, config):
        """Summary line init.

        Extended description of function.
        """
        self.path = pathlib.Path(path)
        self.dir = self.path.parent
        super().__init__(**config)

    def __fspath__(self):
        """Summary line fspath.

        Extended description of function.
        """
        return str(self.path)

    @classmethod
    def read(cls, path):
        """Summary line read.

        Extended description of function.
        """
        path = pathlib.Path(path)
        try:
            with open(path, 'r') as config_file:
                config = yaml.safe_load(config_file)
                return cls(path.parent, config=config)
        except IsADirectoryError:
            sys.exit(f'Configuration `{path}` should be a file.')
        except FileNotFoundError:
            sys.exit(f'Configuration `{path}` not found.')
        except Exception as err:
            sys.exit(f'Loading `{path}` raised: `{err}`.')

    def write(self):
        """Summary line write.

        Extended description of function.
        """
        path, _ = os.path.split(self.path)
        os.makedirs(path, exist_ok=True)

        with open(self.path, 'w') as config_file:
            yaml.dump(dict(self), config_file)
