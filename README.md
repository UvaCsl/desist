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

Please make sure to properly acknowledge `GNU Parallel` or `QCG-PilotJob`
depending on your usage:

- [`GNU Parallel`](https://www.gnu.org/software/parallel/):
  [`10.5281/zenodo.1146014`](https://doi.org/10.5281/zenodo.1146014) and
  [citation notice](https://git.savannah.gnu.org/cgit/parallel.git/tree/doc/citation-notice-faq.txt)
- [`QCG-PilotJob`](https://github.com/vecma-project/QCG-PilotJob/):
  [license](https://github.com/vecma-project/QCG-PilotJob/blob/develop/LICENSE)

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
