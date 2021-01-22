import os
import pathlib
import yaml
import sys


class Config(dict):
    def __init__(self, path, config):
        self.path = pathlib.Path(path)
        self.dir = self.path.parent
        super().__init__(**config)

    def __fspath__(self):
        return str(self.path)

    @classmethod
    def read(cls, path):
        try:
            path = pathlib.Path(path)
            with open(path, 'r') as config_file:
                config = yaml.safe_load(config_file)
                return cls(path.parent, config=config)
        except IsADirectoryError:
            sys.exit(f'Configuration `{path}` should be a file.')
        except FileNotFoundError:
            sys.exit(f'Configuration `{path}` not found.')

    def write(self):
        path, _ = os.path.split(self.path)
        os.makedirs(path, exist_ok=True)

        with open(self.path, 'w') as config_file:
            yaml.dump(dict(self), config_file)
