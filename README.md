# In Silico Clinical Trial (ISCT) workflow

This repository provides the command `isct` to manage *in silico* clinical
trials. The trial is setup as a discrete event-based simulation pipeline, where
submodules represent separate simulation events within the trial, e.g.
statistical analyses, numerical simulations, etc.

## Installation

The package, and its submodules, can be obtained through Gitlab. For ease of
use, using [SSH keys](https://docs.gitlab.com/ee/ssh/) is preferred, as this
simplifies downloading the submodules.

```bash
ssh://git@gitlab.computationalscience.nl:1022/insist/in-silico-trial.git
git submodule update --init --recursive --progress
```

The `desist` package requires Python version `3.8` or `3.9`. Typically a Python
version is present on the system, if not, it can obtained through the system's
package managers, e.g.

```bash
# for macOS
brew install python@3.8

# for linux
sudo apt-get install python3.8 python3.8-dev
```

To install, simply run `make` and the package should be set up in a local
virtual environment `./venv`. Alternatively, it can be manually installed easily
as well, either inside or outside a virtual environment

```bash
# setup virtual environment
python3 -m pip install virtualenv
python3 -m virtualenv venv
source venv/bin/activate

# install the package locally, -e/--editable to enable easy development
pip install . -e
```

To verify if the installation worked evaluate `isct --help` on the
command-line to obtain the application's usage.

```
Usage: isct [OPTIONS] COMMAND [ARGS]...

  des-ist.

  Discrete Event Simulation for In Silico computational Trials.

  This command-line utility supports evaluation of in silico simulation of
  virtual patient cohorts. The utility provides commands to create, run, and
  analyse in silico trials.

Options:
  -v, --verbose  Increase verbosity: shows all `DEBUG` logs.
  --log PATH     Path where log files are written to.
  --help         Show this message and exit.

Commands:
  container  The container subcommand.
  patient    The patient subcommand.
  trial      The trial subcommand.
```

## Usage

To obtain general usage information: `isct --help` or for more specific usage
per command `isct <command> --help` with often used commands: `container`,
`patient`, and `trial`. The provide utilities to interact at respectively the
container, patient, and trial levels.

For specific details on how to use these commands, refer to the corresponding
documentation pages. The can be accessed online: `TODO`, generated locally using
`make docs`, or by inspecting their source
[`docs/source/`](https://gitlab.computationalscience.nl/insist/in-silico-trial/-/tree/update-docs/docs/source).

## Documentation

More in depth documentation can be found at:
`https://insilicostroketrial.eu/insist_docs/.` (Hosted documentation is not yet
up to date: issue #18)

## Pipeline status

Package | Pipeline
--- | ---
`in-silico-trial` | ![pipeline](https://gitlab.computationalscience.nl/insist/in-silico-trial/badges/master/pipeline.svg)
`virtual_patient_generation` | ![pipeline](https://gitlab.computationalscience.nl/insist/virtual_patient_generation/badges/master/pipeline.svg)
`place_clot` | ![pipeline](https://gitlab.computationalscience.nl/insist/place_clot/badges/master/pipeline.svg)
`1D-blood-flow` | ![pipeline](https://gitlab.computationalscience.nl/insist/1d-blood-flow/badges/master/pipeline.svg)
`perfusion_and_tissue_damage` | ![pipeline](https://gitlab.computationalscience.nl/insist/perfusion_and_tissue_damage/badges/master/pipeline.svg)
`thrombo-sis-lysis` | ![pipeline](https://gitlab.computationalscience.nl/insist/thrombo-sis-lysis/badges/master/pipeline.svg)
`thrombectomy` | ![pipeline](https://gitlab.computationalscience.nl/insist/thrombectomy_python_rs/badges/master/pipeline.svg)
`in-silico-trial-outcome` | ![pipeline](https://gitlab.computationalscience.nl/insist/in-silico-trial-outcome/badges/master/pipeline.svg)
`patient-outcome-model` | ![pipeline](https://gitlab.computationalscience.nl/insist/patient-outcome-model/badges/master/pipeline.svg)
