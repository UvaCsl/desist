"""
Usage:
  isct trial create TRIAL [--prefix=PATIENT] [-n=NUM] [-fv] [--seed=SEED]
  isct trial plot TRIAL

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
"""

from docopt import docopt

import sys
import os
import shutil
import yaml
from pathlib import Path

from subprocess import call

from schema import Schema, Use, Or, And, SchemaError

def plot_trial(path):
    """Generate a graph-like visualisation of the trial directory."""

    if not os.path.isdir(path):
        exit(f"Cannot make plot of non-existing directory '{path}'")

    # import graphviz here, as only `plot_trial` depends on it.
    try:
        from graphviz import Digraph
    except ImportError:
        exit(f"Cannot import 'graphviz' package")

    # check if `dot` is present, cannot generate graph without it
    # FIXME: if `dot` is not present, simply write out the plain `.dot` file.
    if shutil.which("dot") is None:
        exit(f"'dot' from graphviz seems not available'")

    # create graph instance of trial
    trial_name = os.path.basename(path)
    g = Digraph(trial_name, filename=path.joinpath("graph.gv").absolute())
    g.attr(rankdir = "LR")

    # populate graph from trial -> patient ->  status
    for patient, dirs, files in os.walk(path):

        # sort by name, such that the graph is orded as well
        dirs.sort()

        # skip top directory
        if patient == str(path.absolute()):
            continue

        # directory name
        p_dir = os.path.basename(patient)

        # patient parameters from configuration file
        with open(Path(patient).joinpath("patient.yml"), "r") as configfile:
            c = yaml.load(configfile, yaml.SafeLoader)

        # setup label and attach to graph
        label = f"{p_dir}/ | id: {c['id']} | done: {c['status']}"
        g.node(p_dir, shape="record", label=label)
        g.edge(trial_name, p_dir)

    # write `graph.gv`, `graph.gv.pdf` and show pdf immediately
    # FIXME: prevent direct visualisation by default, breaks if no screen is
    # attached to the current session
    g.view()


def trial():
    """Provides comamnds for interaction with in-silico trials."""
    # parse command-line arguments
    args = docopt(__doc__)

    # schema for argument validation
    schema = Schema(
            {
                '-n': Use(int, error='Only integer number of patients'),
                '-f': Use(bool),
                '-v': Use(bool),
                '--prefix': Use(str, error='Only string prefixes are allowed'),
                '--seed': Use(int, error='Only integer random seeds allowed'),
                str: object, # all other inputs doesnt  matter yet
                }
    )

    # validate arguments
    try:
        args = schema.validate(args)
    except SchemaError as e:
        print(e)
        exit(__doc__)

    # extract variables
    path = Path(args['TRIAL'])
    overwrite = args['-f']
    prefix = args['--prefix'].replace(" ", "_") # prevents spaces in paths
    num_patients = args['-n']
    verbose = args['-v']
    seed = args['--seed']

    # switch operations based on commands
    if args['plot']:
        exit(plot_trial(path.absolute()))

    # require explicit -f to overwrite existing directories
    if os.path.isdir(path) and not overwrite:
        print(f"Trial '{path}' already exist. Provide -f to overwrite")
        exit(__doc__)

    # clear out old, existing path
    if os.path.isdir(path):
        shutil.rmtree(path)

    # setup trial folder
    try:
        os.makedirs(path)
    except OSerror as e:
        exit(f"Creation of the directory '{path}' failed: '{e}'")

    # populate configuration file
    config = {
            'patients_directory': str(path.absolute()),
            'prefix': prefix,
            'number': num_patients,
    }

    # dump trial configuration to disk
    with open(path.joinpath("trial.yml"), "w") as outfile:
        yaml.dump(config, outfile)

    # create patients configuration files
    for i in range(num_patients):
        cmd = ['python3', 'isct.py', 'patient', 'create', str(path.absolute()), '--id', str(i), '--seed', str(seed), '--config-only']
        if verbose:
            print(" ".join(cmd))

        call(cmd)

    # batch generate all configuration files
    # this runs through docker only once; and not for every patient
    dirs = ["/patients/"+os.path.basename(d[0]) for d in os.walk(path)][1:]
    dirs.sort()
    cmd = ["docker", "run", "-v", f"{path.absolute()}:/patients/", "virtual_patient_generation"] + dirs
    if verbose:
        print(" ".join(cmd))

    call(cmd)


if __name__ == "__main__":
    exit(trial())















