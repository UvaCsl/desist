# `desist`: Discrete Event Simulation for In Silico Trials

`desist` manages running large-scale simulation pipelines for event-based *in
silico* clinical trials, where it supports users in creating, running, and
analysing *in silico* trials. The application assumes the underlying simulation
events are implemented in *containerised* environments, i.e. using either
[Docker](https://www.docker.com/) or
[Singularity](https://sylabs.io/singularity/), and coupled using the provided
[`EventHandler` API](desist/eventhandler/api.py). `desist` implements various
`Runner`s to evaluate the simulations---either sequentially or (massively)
parallel---on a variety of environments: ranging from local machines to
cloud-computing and HPC architectures, where [`GNU
Parallel`](https://www.gnu.org/software/parallel/) and/or
[`QCG-PilotJob`](https://github.com/vecma-project/QCG-PilotJob/) are leveraged
for scheduling, distribution, and parallelisation of the individual simulation
events.

The `desist` packages was originally developed to manage the *in silico*
simulations pipelines within the [INSIST](https://www.insist-h2020.eu/) project
and later made publicly available for extensions to other event-based *in
silico* simulation pipelines. For more information, see the [accompanying
publication](#acknowledgements).

## Installation

The package requires a recent [Python](https://www.python.org) version `>=3.8`. For a (local) development
version it is recommended to setup the package within a (local) [virtual
environment](https://docs.python.org/3/tutorial/venv.html). Then, to install the
package within the virtual environment:

```bash
pip install -e .
```

To verify the installation, run `desist --help` from the virtual environment and
you should see the command-line application's usage instructions.

## Usage

General usage instructions are printed using `desist --help` or more
specifically per command `desist <command> --help`. Typical usage involves
mostly the `trial` command and the `create`, `run`, and `outcome` subcommands.

For more more detailed usage instructions and examples how to use and customise
`desist`, please refer to the [hosted
documentation](https://insilicostroketrial.eu/insist_docs/) (#18) or create the
documentation locally using `make docs` or browsing the (raw) source files in
`docs/source/`.

## Acknowledgements

When using `desist` for your research project, please cite: [`des-ist: A
Simulation Framework to Streamline Event-Based In Silico
Trials`](https://link.springer.com/chapter/10.1007/978-3-030-77967-2_53) (DOI:
`10.1007/978-3-030-77967-2_53`). The corresponding `.bib` file is provided
in [`references.bib`](references.bib).

```
@InProceedings{10.1007/978-3-030-77967-2_53,
author="van der Kolk, Max
and Miller, Claire
and Padmos, Raymond
and Azizi, Victor
and Hoekstra, Alfons",
editor="Paszynski, Maciej
and Kranzlm{\"u}ller, Dieter
and Krzhizhanovskaya, Valeria V.
and Dongarra, Jack J.
and Sloot, Peter M.A.",
title="des-ist: A Simulation Framework to Streamline Event-Based In Silico Trials",
booktitle="Computational Science -- ICCS 2021",
year="2021",
publisher="Springer International Publishing",
address="Cham",
pages="648--654",
isbn="978-3-030-77967-2"
}
```

Please make sure to properly acknowledge `GNU Parallel` or `QCG-PilotJob`
depending on your usage:

- [`GNU Parallel`](https://www.gnu.org/software/parallel/):
  [`10.5281/zenodo.1146014`](https://doi.org/10.5281/zenodo.1146014) and
  [citation notice](https://git.savannah.gnu.org/cgit/parallel.git/tree/doc/citation-notice-faq.txt)
- [`QCG-PilotJob`](https://github.com/vecma-project/QCG-PilotJob/):
  [license](https://github.com/vecma-project/QCG-PilotJob/blob/develop/LICENSE)
