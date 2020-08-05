# In Silico Clinical Trial (ISCT) workflow 
This repository provides the command `isct` to manage in silico clinical trials. 
The trial is setup as an event-based simulation, where the submodules correspond
to separate events (e.g statistical analysis, simulations, etc.) of the trial. 

## Installation 
To install the package first clone this repository and its submodules. Either 
through `https` (default): 
```
git clone https://gitlab.computationalscience.nl/insist/in-silico-trial.git
cd in-silico-trial
mv .gitmodules_https .gitmodules
```
or through `ssh` if you have setup `ssh-keys`: 
```
ssh://git@gitlab.computationalscience.nl:1022/insist/in-silico-trial.git
```
Then recursively update the submodules: 
``` 
git submodule update --init --recursive --progress
```
The package can be installed either in the global Python environment or within
a local, virtual environment. To (optionally) install the virtual environment, 
first run 
```
python3 -m pip install virtualenv
python3 -m virtualenv venv 
source venv/bin/activate 
```
This creates the virtual environment in which `isct` will be installed. This 
keeps the `isct` environment completely separate from any other Python 
environments. Note, you need to ensure the virtual environment is active
before you can run any of the following command. Typing `deactivate` leaves the
virtual environment. 

Now, we can locally install the `isct` package and its requirements. Run the
following steps within the `venv` if you desire to use the virtual environment. 
Note: `-e` (or `--editable`) allows to edit the package and have its changes
be reflected in `isct`. Otherwise we are required to reinstall the package 
after any change. If you do not intent to edit the package `-e` can be omitted. 

From within `in-silico-trial/` the package and the (most) essential requirements
are installed by: 
```
pip install -e . 
```
This installs `isct` with the bare minimum requirements, which disables some
non-essential functionalities of the `isct` command with the benefit of 
installing (slightly) less dependencies. However, it is recommended to install
all its requirements as given in `requirements.txt` to enable all features
of `isct` by evaluating: 
```
pip install -r requirements.txt
```
This provides the `isct` command to manage the in-silico trials. To check the 
command is present, run 
```
isct help 
```
to show it usage. If you installed all requirements and want to perform a more
throurough verification, you can evaluate the tests: 
```
pytest --cov=workflow 
```

### Building container images 
The individual simulations of the event-based simulation chain are performed 
within their own containerised environment. The `isct` command supports both
Docker and Singularity images to be used. Roughly each submodule has its own
container image based on a `Dockerfile` or `singularity.def` definitions file
for Docker and Singularity, respectively. These files describe the details
of the container images which we are going to build. 

To build these containers either Docker or Singularity need to be present on 
the local system. Note, in the future the Singularity images can be downloaded
directly from Gitlab (after issue #37 is merged). To build a container we 
simply pass a directory of the submodule to the `isct container build` 
command, such as 
```
isct container build $CONTAINER -v
```
To build the Singularity containers we need to provide a location where to 
store the resulting image files by passing the `-s` or `--singularity` file
followed by the container path `$CONTAINERPATH`
```
isct container build $CONTAINER -v -s $CONTAINERPATH
```
Note, multiple container paths can be provided to build multiple containers 
directly, or even in parallel using `--gnu-parallel`, such as 
```
isct container build software/* -v -s $CONTAINERPATH --gnu-parallel | parallel -j+0
```

## Usage 
```
$ isct 

Usage: isct [--version] [--help] [--log=<path>] <command> [<args>...]

Options:
   -h, --help       Shows the usage of the `isct` command.
   --version        Shows the version number.
   --log=<path>     Path to store the logfile [default: /tmp/isct.log].

The most commonly used `isct` commands are:
    container   Interact with Docker/Singularity containers of event modules.
    help        Show help for any of the commands.
    patient     Interact with individual virtual patients.
    trial       Interact with trials.

See `isct help <command>` for more information on a specific command.
```
The package provides subcommands to manage the in silico trials.

### Trial
```
$ isct help trial 

Usage:
  isct trial create TRIAL [--prefix=PATIENT] [-n=NUM] [-fv] [--seed=SEED] [--singularity=DIR]
  isct trial ls TRIAL [-r | --recurse]
  isct trial plot TRIAL [--show]
  isct trial run TRIAL [-x] [-v] [--gnu-parallel] [--singularity=DIR]
  isct trial status TRIAL

Arguments:
    PATH        A path on the file system.
    TRIAL       Path to trial directory.
    DIR         A path on the file system containing the singularity images.

Options:
    -h, --help              Shows the usage of `isct trial`.
    --version               Shows the version number.
    --prefix=PATIENT        The prefix for the patient directory [default: patient].
    -n=NUM                  The number of patients to generate [default: 1].
    -f                      Force overwrite existing trial directory.
    -v                      Set verbose output.
    --seed=SEED             Random seed for the trial generation [default: 1].
    --show                  Directly show the resulting figure [default: false].
    -x                      Dry run: only log the command without evaluating.
    -r, --recurse           Recursivly show content of trial directory.
    --gnu-parallel          Forms the outputs to be piped into gnu parallel, e.g. `isct trial run TRIAL --gnu-parallel | parallel -j+0`
    -s, --singularity=DIR   Use singularity as containers by providing the directory `DIR` of the Singularity containers.
```

### Parallel execution
The `isct` command currently supports basic parallel execution of patient 
simulations by evaluating each patient in paralle using [GNU 
`parallel`](https://www.gnu.org/software/parallel/parallel_tutorial.html). 
For `isct container build` and `isct trial run` the `--gnu-parallel` flag 
enables that `isct` writes the commands to `stdout`, rather then evaluating
the commands directly. This allows to pipe these commands into `parallel` 
and let `paralllel` control the parallel execution of the commands that 
are streamed over `stdout`. The `parallel` command can be installed on a 
system using `apt install parallel` for Linux and `brew install parallel` 
on macOS. 

The following examples consider `parallel` for running small to intermediate
sized batches of patient simulations on either local machines or on smaller
remote systems. Support for running these jobs on larger HPC-like systems is 
to be added later. The following examples assume both `isct` and `parallel` 
are installed on both the local and remote systems, where both commands are
also available on the current `path` for simplicity (i.e. the commands 
`isct` and `parallel` can be evaluated from any directory without explicitly
providing the paths as `/usr/bin/parallel`). 

For illustration, we consider a batch of 20 patients for the `newtrial` 
trial. The directory structure of the trial can be build using Docker: 
```
isct trial create newtrial -n 20 -v
``` 
or by Singularity where the Singularity containers are stored in a path 
`$CONTAINERS` on the relevant system: 
```
isct trial create newtrial -n 20 -v -s $CONTAINERS
``` 
There are multiple approaches to running such a batch of patient 
simulations. The simplest being the sequential evaluation of all required
simulations:
```
isct trial run newtrial -v -s $CONTAINERS
```
This traverses the `newtrial` directory and evaluates each simulation 
sequentially, where the overal progress can be monitored with 
`isct trial status newtrial`. The `isct` command evaluates each set 
of patient simulations individually. To parallelise this operation, 
we can pipe these commands into `parallel` as follows: 
```
isct trial run newtrial -v -s $CONTAINERS --gnu-parallel | parallel -j2 
```
The first part writes each individual patient command over `stdout`, 
which is read by `parallel`. Then, it is up to `parallel` to evaluate
the commands in parallel. This command accepts many parameters, as
outlined in its [manual](https://www.gnu.org/software/parallel/parallel_tutorial.html).
When running this command directly on a local or remote system, we can
supply `j+0` to use the same number of threads as (detected) CPUs, or 
we can be a bit more specific and provide `-jn` with `n` simultaneous 
allowed threads. 

Alternatively, `parallel` provides means to distribute the computations 
directly from a local machine over `ssh` to any available remote servers. 
In this case `parallel` is in charge of distributing the patient 
directories towards the remote machine and starting all simulations. For
example, we can attempt to distribute the 20 patient simulations over
a known machine on `ssh`, for now indicated as `$SERVER1`. The simulation is
started as 
```
isct trial run $TRIAL -v --gnu-parallel -s containers/ | parallel -S 2/$SERVER1 --basefile $TRIAL --workdir $WORKDIR --ungroup -j2 
```
with the following flags and settings
- `$TRIAL`: a trial directory, in this example equal to `newtrial`;
- `WORKDIR`: the working directory on the remote machine. It is assumed this 
directory contains a folder (or symbolic link) to a folder named `containers`
(note: for now this has to be identical to the local machine) such that `isct` 
can find the Singularity containers;
- `2/$SERVER1`: provides the server to use and indicates to use 2 CPUs;
- `-j2`: allow two simulataneous jobs on the remote machine 
- `--basefile $TRIAL`: indicate to `parallel` to copy the generated virtual 
patients from `$TRIAL` towards the working directory `$WORKDIR` on the remote
machine. 

This command requires an open connection until all jobs are finalised and is 
most suited for shorter jobs to distribute. Note, the `parallel` does not 
clean up all directories and the results of the simulation remain present on 
the remote system for now. 

### Documentation 
More in depth documentation can be found at: https://insilicostroketrial.eu/insist_docs/. 

(Hosted documentation is not yet up to date: issue #18)

## Pipeline status 
(CI/CD might not be accurate at the moment: issue #16)

Package | Pipeline | Coverage
--- | --- | ---
in-silico-trial | ![pipeline](https://gitlab.computationalscience.nl/insist/in-silico-trial/badges/master/pipeline.svg) | ![coverage](https://gitlab.computationalscience.nl/insist/in-silico-trial/badges/master/coverage.svg)
virtual_patient_generation | ![pipeline](https://gitlab.computationalscience.nl/insist/virtual_patient_generation/badges/master/pipeline.svg) | ![coverage](https://gitlab.computationalscience.nl/insist/virtual_patient_generation/badges/master/coverage.svg)
Place clot | ![pipeline](https://gitlab.computationalscience.nl/insist/place_clot/badges/master/pipeline.svg) | ![coverage](https://gitlab.computationalscience.nl/insist/place_clot/badges/master/coverage.svg)
1D blood flow | ![pipeline](https://gitlab.computationalscience.nl/insist/1d-blood-flow/badges/master/pipeline.svg) | ![coverage](https://gitlab.computationalscience.nl/insist/1d-blood-flow/badges/master/coverage.svg)
darcy_multi-comp | ![pipeline](https://gitlab.computationalscience.nl/insist/darcy_multi-comp/badges/master/pipeline.svg) | ![coverage](https://gitlab.computationalscience.nl/insist/darcy_multi-comp/badges/master/coverage.svg)
cell_death_model | ![pipeline](https://gitlab.computationalscience.nl/insist/cell_death_model/badges/master/pipeline.svg) | ![coverage](https://gitlab.computationalscience.nl/insist/cell_death_model/badges/master/coverage.svg)
thrombo-sis-lysis | ![pipeline](https://gitlab.computationalscience.nl/insist/thrombo-sis-lysis/badges/master/pipeline.svg) | ![coverage](https://gitlab.computationalscience.nl/insist/thrombo-sis-lysis/badges/master/coverage.svg)
thrombectomy | ![pipeline](https://gitlab.computationalscience.nl/insist/thrombectomy_python_rs/badges/master/pipeline.svg) | ![coverage](https://gitlab.computationalscience.nl/insist/thrombectomy_python_rs/badges/master/coverage.svg)
In silico trial outcome module | ![pipeline](https://gitlab.computationalscience.nl/insist/in-silico-trial-outcome/badges/master/pipeline.svg) | ![coverage](https://gitlab.computationalscience.nl/insist/in-silico-trial-outcome/badges/master/coverage.svg)
Patient outcome module | ![pipeline](https://gitlab.computationalscience.nl/insist/patient-outcome-model/badges/master/pipeline.svg) | ![coverage](https://gitlab.computationalscience.nl/insist/patient-outcome-model/badges/master/coverage.svg)
