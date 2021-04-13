Architecture
============

The ``desist`` contains all its source code within ``desist/`` inside the root
directory of the package with matching tests in ``tests/``. The package code is
split into two parts: the command-line application (``cli_*.py``) and the
backing implementation in the other python files.

The command-line utility is written using `Click
<https://click.palletsprojects.com/en/7.x/>`_. This is mostly a wrapper around
the backing implementation and not described in much detail here. The exported
commands are documented in :doc:`cmd`.

The code is structured as follows, which is reflected by the tests (``tests/``)

.. code-block:: bash

    desist/
        # the functionality related to ``click`` command-line utility
        cli/

        # the eventhandling and API definitions
        eventhandler/

        # the core ``isct`` functionality
        isct/

With the fundamental implementation in ``isct/`` out as:

.. code-block:: python

    config.py       # abstract configuration file
    patient.py      # expresses a virtual patient as its configuration
    trial.py        # expresses a *in silico* trials as its configuration

    container.py    # abstract container functionality
    docker.py       # implements the abstract container for Docker
    singularity.py  # implements the abstract container for Singularity

    runner.py       # various implementation to run commands (subshell, ...)
    events.py       # represents a trial in `events` and `modules`
    utilities.py    # generic utility functions

There are two fundamental classes within ``desist``: the configuration file
abstraction: :py:class:`~isct.config.Config` and the container abstraction
:py:class:`~isct.container.Container`. These classes provide the abstract
interface for representing trials and patients by means of their corresponding
configuration files. Similarly, :py:class:`~isct.container.Container`, holds the
abstract implementation to represent a containerised environment, e.g. Docker
and Singularity, and the necessary routines to evaluate commands within these
environments.

Configuration files
-------------------

Fundamentally, the *in silico* trials have the layout:

.. code-block:: bash

    /trial/
        trial.yml
        patient_00000/
            patient.yml
        patient_00001/
            patient.yml
        ...

This allows to express both the trial and patients simply by their configuration
files, as derived from :py:class:`~isct.config.Config`.

Containerised environments
--------------------------

In ``desist`` the choice is made to use containerised environments to separate
the various possible simulation steps (read: events) within an *in silico*
pipeline. It is assumed that the simulation code, that is to be containerised,
is placed inside a root directory containing either a ``Dockerfile`` and/or a
``singularity.def`` file describing the requirements of the resulting
environment. After constructing these individual containers, ``desist`` can
invoke these containers to evaluate an event's simulation.

The basic skeleton of a container functionality, i.e. creating and running, is
given in the abstract implementation :py:class:`~isct.container.Container` and
is made specific for each type in: :py:class:`~isct.docker.Docker` and
:py:class:`~isct.singularity.Singularity`.
