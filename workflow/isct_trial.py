"""
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
"""

from docopt import docopt

import sys
import os
import shutil
import yaml
from pathlib import Path

from subprocess import call

from schema import Schema, Use, Or, And, SchemaError

from workflow.isct_patient import patient as patient_cmd

def plot_trial(path, args):
    """Generate a graph-like visualisation of the trial directory."""

    if not os.path.isdir(path):
        sys.exit(f"Cannot make plot of non-existing directory '{path}'")

    # import graphviz here, as only `plot_trial` depends on it.
    try:
        from graphviz import Digraph
    except ImportError:
        sys.exit(f"Cannot import 'graphviz' package")

    # check if `dot` is present, cannot generate graph without it
    # FIXME: if `dot` is not present, simply write out the plain `.dot` file.
    if shutil.which("dot") is None:
        sys.exit(f"'dot' from graphviz seems not available'")

    # create graph instance of trial
    trial_name = os.path.basename(path)
    g = Digraph(trial_name, filename=path.joinpath("graph.gv").absolute())
    g.attr(rankdir = "LR")

    # populate graph from trial -> patient ->  status
    for trial, patients, files in os.walk(path):

        # patients are sorted, such that output graph is sorted as well
        patients.sort()

        for patient in patients:

            # patient parameters from configuration file
            p_dir = Path(trial).joinpath(patient)
            with open(p_dir.joinpath("patient.yml"), "r") as configfile:
                c = yaml.load(configfile, yaml.SafeLoader)

            # setup label and attach to graph
            label = f"{patient}/ | id: {c['id']} | done: {c['status']}"
            g.node(patient, shape="record", label=label)
            g.edge(trial_name, patient)

        break # prevent recursion of `os.walk()`

    # write `graph.gv`, `graph.gv.pdf` and option to show pdf
    g.render(view=args['--show'])

def trial(argv):
    """Provides comamnds for interaction with in-silico trials."""
    # parse command-line arguments
    args = docopt(__doc__, argv=argv)

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
        sys.exit(__doc__)

    # extract variables
    path = Path(args['TRIAL'])
    overwrite = args['-f']

    # prevent spaces in directories, set to default for empty
    prefix = args['--prefix'].replace(" ", "_")
    if prefix == "''":
        prefix = "patient"

    num_patients = args['-n']
    verbose = args['-v']
    seed = args['--seed']

    # switch operations based on commands
    if args['plot']:
        plot_trial(path.absolute(), args)
        return

    # require explicit -f to overwrite existing directories
    if os.path.isdir(path) and not overwrite:
        print(f"Trial '{path}' already exist. Provide -f to overwrite")
        sys.exit(__doc__)

    # clear out old, existing path
    if os.path.isdir(path):
        shutil.rmtree(path)

    # setup trial folder
    os.makedirs(path, exist_ok=True)

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
        cmd = ['patient', 'create', str(path.absolute()), '--id', str(i), '--seed', str(seed), '--config-only']
        patient_cmd(cmd)

    # batch generate all configuration files
    # this runs through docker only once; and not for every patient
    dirs = ["/patients/"+os.path.basename(d[0]) for d in os.walk(path)][1:]
    dirs.sort()
    cmd = ["docker", "run", "-v", f"{path.absolute()}:/patients/", "virtual_patient_generation"] + dirs
    if verbose:
        print(" ".join(cmd))

    call(cmd)

if __name__ == "__main__":
    sys.exit(trial(sys.argv[1:]))
