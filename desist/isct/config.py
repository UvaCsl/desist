"""Configuration dictionary class.

This module contains the base configuration class for
:class:`~isct.patient.Patient` and :class:`~isct.trial.Trial`. The
configuration inherits from :class:`dict` to provide dictionary-like behaviour
and provides the :meth:`~isct.config.Config.read` and
:func:`~isct.config.Config.write` functionalities to simplify reading and
writing of the configuration files.
"""

import collections
import pathlib

import desist.isct.utilities as utilities


class Config(dict):
    """Configuration class.

    This class extends a :obj:`dict` with functions to read/write the
    underlying dictionary to the YAML format.
    """

    def __init__(self, path, config):
        """Initialise from provided configuration at path.

        Args:
            path (str): Path to the configuration file.
            config (dict): Initialise configuration with dictionary.
        """
        self.path = pathlib.Path(path)
        super().__init__(**config)

        # FIXME: consider storing a `isct` version / git hash by default

    @property
    def path(self):
        """Path pointing to patient configuration file."""
        return self._path

    @path.setter
    def path(self, path):
        """Store path to patient configuration file as `pathlib.Path`."""
        self._path = pathlib.Path(path)

    @property
    def dir(self):
        """Return the directory as the parent of the file's path."""
        return self.path.parent

    def __fspath__(self) -> str:
        """Return the file system path of the :class:`Config`."""
        return str(self.path)

    @classmethod
    def read(cls, path):
        """Initialises :class:`Config` from the provided YAML file.

        Attempts to parse the YAML file from ``path`` to a dictionary and on
        success returns an initialised :class:`Config`. If parsing the
        YAML file did not succeed, the routine exits.

        Args:
            path (str): Path to YAML file.
        """
        path = pathlib.Path(path)
        config = utilities.read_yaml(path)

        assert isinstance(config, collections.abc.Mapping), """To represent a
        configuration file the contents read from the YAML file `{path}` should
        be represented by a `collections.abc.Mapping` type and not a
        `{type(config)}`."""

        return cls(path.parent, config=config)

    def write(self):
        """Writes the configuation to disk as YAML.

        The :class:`Config` is written as dictionary to disk. The file is
        written in the YAML format.

        The directory :attr:`Config.dir` is created when not yet present.
        """
        utilities.write_yaml(self.path, dict(self))
