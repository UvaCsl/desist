Discrete Event Simulation for *In Silico* Trials: ``desist``
============================================================

``desist`` provides a command-line utility to support generation, evaluation,
and analysis of *in silico* trials. The package has been developed in context of
the `INSIST <https://www.insist-h2020.eu/>`_ project.

Installation
------------

The package requires Python 3 and is tested with ``3.8`` and ``3.9``. A Makefile
is provided to install the package locally.

.. code-block:: bash

    git clone https://gitlab.computationalscience.nl/insist/in-silico-trial
    cd in-silico-trial
    make

Afterwards the package is installed within a virtual environment and should be
available on the path

.. code-block:: bash

    # activate environment
    source ./venv/bin/activate

    # test installation
    desist --help

Usage
-----

A brief overview of the usage of the commands available in ``desist`` is
obtained by ``desist --help``, with specific usage instructions for individual
commands, e.g. to build containers, with ``desist container --help``.

.. code-block:: bash

    # general usage instructions
    desist --help

    # command specific instructions
    desist container --help
    desist trial --help
    desist patient --help

The documentation is also available here: :doc:`cmd`.

Examples
--------

Multiple examples are provided, for example on using ``desist`` to create
simulation containers :doc:`tutorial-containers`, to create virtual cohorts and
evaluate their simulations :doc:`tutorial-trials`, and combining ``desist`` with
VVUQ: :doc:`tutorial-vvuq`.

Extending ``desist``
--------------------

The main implementation of ``desist`` is tailored for the discrete event
simulation pipelines as encountered in the INSIST project. However, the package
contains various useful abstractions that can be reused for other event-driven
simulation pipelines. The general layout and concepts behind the code are
discussed in :doc:`architecture`, where the class specific documentation is
given in :doc:`reference`.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   tutorial-containers
   tutorial-trials
   tutorial-vvuq
   architecture
   reference
   cmd


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
