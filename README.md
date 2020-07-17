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
isct --help 
```
to show it usage. If you installed all requirements and want to perform a more
throurough verification, you can evaluate the tests: 
```
pytest --cov=workflow 
```


## Usage 
```
isct --help 

usage: isct [--version] [--help] <command> [<args>...]

options:
   -h, --help  Shows the usage.
   --version  Shows the version number.

The most commonly used isct commands are:
    trial     Interact with trials.
    patient   Interact with individual virtual patients.

See `isct help <command>` for more information on a specific command.
```
The package provides subcommands to manage the in silico trials.

### Trial
```
isct help trial 

Usage:
  isct trial create TRIAL [--prefix=PATIENT] [-n=NUM] [-fv] [--seed=SEED]
  isct trial plot TRIAL [--show]

Arguments:
    PATH        A path on the file system.
    TRIAL       Path to trial directory.

Options:
    -h, --help          Show this screen.
    --version           Show version.
    --prefix=PATIENT    The prefix for the patient directory [default: patient].
    -n=NUM              The number of patients to generate [default: 1].
    -f                  Force overwrite existing trial directory.
    -v                  Set verbose output.
    --seed=SEED         Random seed for the trial generation [default: 1].
    --show              Directly show the resulting figure [default: false].
```

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
