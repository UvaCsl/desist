Discrete Event Simulation for *In Silico* trials
================================================

.. figure:: _static/logo.svg
     :align: center

``desist`` manages running large-scale simulation pipelines for event-based *in
silico* clinical trials, where it supports users in creating, running, and
analysing *in silico* trials. The application assumes the underlying simulation
events are implemented in *containerised* environments, i.e. using either
`Docker <https://www.docker.com/>`_ or `Singularity
<https://sylabs.io/singularity/>`_, and coupled using the provided
:doc:`EventHandler <api>` API. ``desist`` implements various :doc:`Runner
<runner>` implementations to evaluate the simulations---either sequentially or
(massively) parallel---on a variety of environments: ranging from local machines
to cloud-computing and HPC architectures, where `GNU Parallel
<https://www.gnu.org/software/parallel/>`_ and/or `QCG-PilotJob
<https://github.com/vecma-project/QCG-PilotJob/>`_ are leveraged for scheduling,
distribution, and parallelisation of the individual simulation events.

The ``desist`` packages was originally developed to manage the *in silico*
simulations pipelines within the `INSIST <https://www.insist-h2020.eu/>`_
project and later made publicly available for extensions to other event-based
*in silico* simulation pipelines. For more information, see
:ref:`acknowledgements`.

Installation
------------

The package requires a recent `Python <https://www.python.org>`_ version
``>=3.8``. For a (local) development version it is recommended to setup the
package within a (local) `virtual environment
<https://docs.python.org/3/tutorial/venv.html>`_. Then, to install the package
within the virtual environment:

.. code-block:: bash

   # clone the repository
   git clone https://gitlab.computationalscience.nl/insist/in-silico-trial
   cd in-silico-trial

   # setup a virtual environment (there are many approach of doing so)
   python -m venv venv
   . venv/bin/activate

   # install desist
   pip install -e .

To enable the `QCG-PilotJob <https://github.com/vecma-project/QCG-PilotJob/>`_
runner you can include the ``[qcg]`` feature:

.. code-block:: bash

   pip install -e .[qcg]

To verify the installation, run ``desist --help`` from the virtual environment
and you should see the command-line application's usage instructions.

Usage
-----

General usage instructions are printed using ``desist --help`` or more
specifically per command ``desist <command> --help``. Typical usage involves
mostly the ``trial`` command and the ``create``, ``run``, and ``outcome``
subcommands.

.. code-block:: bash

    desist --help
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
   pipelines
   reference
   cmd

.. _acknowledgements:

Acknowledgements and citation
-----------------------------

When using ``desist`` for your research project, please cite: ``des-ist: A
Simulation Framework to Streamline Event-Based In Silico Trials`` (DOI:
``10.1007/978-3-030-77967-2_53``). The corresponding ``.bib`` file is provided
in ``references.bib``.

Please make sure to properly acknowledge ``GNU Parallel`` or ``QCG-PilotJob``
depending on your usage.

Publications using ``desist``:

- `Uncertainty Quantification of Coupled 1D Arterial Blood Flow and 3D Tissue
  Perfusion Models Using the INSIST Framework
  <https://link.springer.com/chapter/10.1007%2F978-3-030-77980-1_52>`_
- `In silico trials for treatment of acute ischemic stroke: Design and
  implementation <https://doi.org/10.1016/j.compbiomed.2021.104802>`_

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
