# Discrete Event Simulation for In Silico Trials `desist`

This repository provides the command `desist` to manage *in silico* clinical
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
pip install -e .
```

To verify if the installation worked evaluate `desist --help` on the
command-line to obtain the application's usage.

```
Usage: desist [OPTIONS] COMMAND [ARGS]...

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

To obtain general usage information: `desist --help` or for more specific usage
per command `desist <command> --help` with often used commands: `container`,
`patient`, and `trial`. The provide utilities to interact at respectively the
container, patient, and trial levels.

For specific details on how to use these commands, refer to the corresponding
documentation pages. The can be accessed online: `TODO`, generated locally using
`make docs`, or by inspecting their source
[`docs/source/`](https://gitlab.computationalscience.nl/insist/in-silico-trial/-/tree/update-docs/docs/source).

## INSIST Trial

The `des-ist` package was developed for the streamlining of the INSIST
project. The corresponding simulation modules and pipelines are provided
at in a separate repository [`insist-trials`](https://gitlab.computationalscience.nl/insist/insist-trials).

## Documentation

More in depth documentation can be found at:
`https://insilicostroketrial.eu/insist_docs/.` (Hosted documentation is not yet
up to date: issue #18)

## Acknowledgements

When using `desist` for your research project, please cite: [`des-ist: A
Simulation Framework to Streamline Event-Based In Silico
Trials`](https://link.springer.com/chapter/10.1007/978-3-030-77967-2_53) with
DOI: `10.1007/978-3-030-77967-2_53`. The corresponding "`.bib`" file is provided
in [`references.bib`](references.bib).

## Change log

2021/06/22

- The environment is passed into the `LocalRunner`, which is also forwarded by
  `sudo` through passing the `-E` flag.
- Generic files and/or directories place inside a trial directory are ignored
  and not attempted to be processed as patients in `trial run` and similar
  commands.

2021/06/30

- Add support for [`QCG-PilotJob`](https://github.com/vecma-project/QCG-PilotJob)
  as a runner for the trials.
- Add the `--qcg` flag to invoke the `QCGRunner` to run trials.

2021/07/02

- Change default archive filename `trial_data.RData` to
  `trial_outome_data.RData`.

2021/07/12

- Event pipelines are propagated from the criteria files (`criteria.yml`) into
  the patient configuration files (`trial/patient_*/patient.yml`) such that
  different pipelines can be defined directly in the criteria files.
- Providing `--clean-files` does not accidentally clean up the files in
  combination with the `-x` (dry-run) flag.

2021/07/26

- Change `--keep-files/--clean-files` toggles to `--clean-files OPTION` where
  three choices are possible: `none`, `1mb`, or `all`. The first two, `none` and
  `1mb` mimic the original behaviour with `--keep-files/--clean-files`
  respectively. The new `all` flag performs more aggressive file cleaning and
  removes any file---except for YAML files with `.yml` or `.yaml`
  suffix---regardless of the required disk space.
- Add a [`CleanFiles`](desist/isct/utilities.py) enumerated type to keep track
  of file cleaning modes.
- Add a [`FileCleaner`](desist/isct/utilities.py) utility class that handles
  file cleaning and supersedes the separate `clean_large_files` utility
  function.
- Add `Runner.wait()` function to avoid type assertion in `QCGRunner.run()`.
