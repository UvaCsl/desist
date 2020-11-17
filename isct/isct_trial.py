"""
Usage:
  isct trial create TRIAL [--prefix=PATIENT] [--criteria=FILE] [-n=NUM] [-fv]
                          [--seed=SEED] [--singularity=DIR] [--root]
  isct trial ls TRIAL [-r | --recurse]
  isct trial outcome TRIAL [-xv] [--singularity=DIR] [--root]
  isct trial plot TRIAL [--show]
  isct trial reset TRIAL
  isct trial run TRIAL [-x] [-v] [--gnu-parallel] [--singularity=DIR]
                       [--validate] [--root]
  isct trial status TRIAL

Arguments:
    PATH        A path on the file system.
    TRIAL       Path to trial directory.
    DIR         A path on the file system containing the singularity images.

Options:
    -h, --help              Shows the usage of `isct trial`.
    --version               Shows the version number.
    --prefix=PATIENT        Prefix for patient directory [default: patient].
    --criteria=FILE         YAML file defining inclusion criteria. These will
                            overwrite any values specified by `--seed` and
                            `-n` for the random seed and number of patients.
    -n=NUM                  The number of patients to generate [default: 1].
    -f                      Force overwrite existing trial directory.
    -v                      Set verbose output.
    --seed=SEED             Random seed for the trial generation [default: 1].
    --show                  Directly show the figure [default: false].
    -x                      Dry run: only log the command without evaluating.
    -r, --recurse           Recursivly show content of trial directory.
    --gnu-parallel          Forms the outputs to be piped into gnu parallel,
                            e.g. `isct trial run TRIAL --gnu-parallel |
                            parallel -j+0`
    -s, --singularity=DIR   Use singularity as containers by providing the
                            directory `DIR` of the Singularity containers.
    --validate              Validate the patient YAML configuration file.
    --root                  Flag to indicate root access or user already
                            has permissions. This flag removes the prefixed
                            `sudo` from the Docker containers.
"""

from docopt import docopt

import sys
import os
import shutil
import yaml
import pathlib
import subprocess
import schema
import logging

import isct.utilities as utilities
from .container import new_container
from .patient import Patient, patients_from_trial
from .isct_patient import patient as patient_cmd


def trail_plot(args):
    """Generate a graph-like visualisation of the trial directory."""

    s = schema.Schema({
        'TRIAL': schema.And(schema.Use(str), os.path.isdir),
        str: object,
    })
    try:
        args = s.validate(args)
    except schema.SchemaError as e:
        print(e)
        sys.exit(__doc__)

    # import graphviz here, as only `trail_plot` depends on it.
    try:
        from graphviz import Digraph
    except ImportError:
        sys.exit("Cannot import 'graphviz' package")

    # check if `dot` is present, cannot generate graph without it
    renderPlot = True
    if shutil.which("dot") is None:
        renderPlot = False
        print("The `dot` from graphviz is not present: no figure is rendered.")

    # create graph instance of trial
    path = pathlib.Path(args['TRIAL'])
    trial_name = os.path.basename(path)
    g = Digraph(trial_name, filename=path.joinpath("graph.gv").absolute())
    g.attr(rankdir="LR")

    # populate graph from trial -> patient ->  status
    for trial, patients, files in os.walk(path):

        # patients are sorted, such that output graph is sorted as well
        patients.sort()

        for patient in patients:

            # patient parameters from configuration file
            c = Patient.from_yaml(pathlib.Path(trial).joinpath(patient))

            # setup label and attach to graph
            label = f"{patient}/ | id: {c['id']} | done: {c['status']}"
            g.node(patient, shape="record", label=label)
            g.edge(trial_name, patient)

        break  # prevent recursion of `os.walk()`

    # write `graph.gv`, this can run without `dot` as it does not render yet
    g.save()

    if renderPlot:
        # write `graph.gv.pdf`, this requires `dot` executable
        g.render(view=args['--show'])


def create_trial_config(path, prefix, num_patients, seed):
    """Initialise a dictionary as trial configuration."""

    # to easily get its absolute path
    assert isinstance(path, pathlib.Path)

    # find the sha of `in-silico-trial`
    git_sha = utilities.get_git_hash(utilities.isct_module_path())
    if git_sha == "":
        git_sha = "not_found"

    return {
        'patients_directory': str(path.absolute()),
        'prefix': prefix,
        'sample_size': num_patients,
        'preprocessed': False,
        'git_sha': git_sha,
        'random_seed': seed,
    }


def add_events(patient):
    """Add list of events to a patient configuration file."""


def trial_create(args):
    # schema for argument validation
    s = schema.Schema({
        '-n':
        schema.And(
            schema.Use(int, error='Only integer number of patients'),
            lambda n: n > 0,
            error="Argument `-n` must be a postive non-zero number of patients"
        ),
        '-f':
        schema.Use(bool),
        '-v':
        schema.Use(bool),
        '--prefix':
        schema.Use(str, error='Only string prefixes are allowed'),
        '--seed':
        schema.Use(int, error='Only integer random seeds allowed'),
        '--singularity':
        schema.Or(None, schema.And(schema.Use(str), os.path.isdir)),
        '--root':
        schema.Use(bool),
        '--criteria':
        schema.Or(None, schema.And(schema.Use(str), os.path.isfile)),
        str:
        object,  # all other inputs don't matter
    })

    # validate arguments
    try:
        args = s.validate(args)
    except schema.SchemaError as e:
        print(e)
        sys.exit(__doc__)

    # extract variables
    path = pathlib.Path(args['TRIAL'])
    overwrite = args['-f']

    if args['-v']:
        # print all info levels for user
        logging.getLogger().handlers[0].setLevel(logging.INFO)

    # prevent spaces in directories, set to default for empty
    prefix = args['--prefix'].replace(" ", "_")
    if prefix == "''":
        prefix = "patient"

    num_patients = args['-n']
    seed = args['--seed']

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
    config = create_trial_config(path, prefix, num_patients, seed)

    # Load inclusion criteria if provided and update duplicate variables
    criteria = utilities.read_yaml(args['--criteria'])
    config = {**config, **criteria}

    # sample size and random seed can be present in the criteria files
    num_patients = config.get('sample_size', num_patients)
    seed = config.get('random_seed', seed)

    # dump trial configuration to disk
    with open(path.joinpath("trial.yml"), "w") as outfile:
        yaml.dump(config, outfile)

    # create patients configuration files
    for i in range(num_patients):
        cmd = [
            'patient', 'create',
            str(path.absolute()), '--id',
            str(i), '--seed',
            str(seed), '--config-only'
        ]
        patient_cmd(cmd)

    # batch generate all configuration files
    # this runs through docker only once; and not for every patient
    dirs = ["/patients/" + os.path.basename(d[0]) for d in os.walk(path)][1:]
    dirs.sort()

    c = new_container(args['--singularity'], args['--root'])
    tag = "virtual_patient_generation"

    c.bind_volume(path.absolute(), "/patients/")

    # log command to be executed
    logging.info(f' + {" ".join(cmd)}')

    # only call into the container when its executable is present on a system
    if not c.executable_present():
        logging.critical(f"Cannot reach {c.type}.")
        return

    # check if `virtual-patient-generation` image is available
    if not c.image_exists(tag):
        sys.exit(1)

    # form command to evaluate `virtual-patient-generation`
    cmd = c.run_image(tag, f"{' '.join(dirs)} --seed {seed}")

    # evaluate `virtual-patient-generation` model to fill config files
    utilities.run_and_stream(cmd, logging)

    # Create auxilary files for each patient.
    # TODO: remove the XML export once transitioned to YAML
    for d in [d[0] for d in os.walk(path)][1:]:
        p = Patient.from_yaml(d)
        p.update_defaults()
        p.to_yaml()
        p.to_xml()


def trial_run(args):
    # validate run arguments
    s = schema.Schema({
        '-x':
        bool,
        '-v':
        bool,
        'TRIAL':
        schema.And(schema.Use(str), os.path.isdir),
        '--gnu-parallel':
        bool,
        '--singularity':
        schema.Or(None, schema.And(schema.Use(str), os.path.isdir)),
        '--root':
        schema.Use(bool),
        '--validate':
        bool,
        str:
        object,
    })
    try:
        args = s.validate(args)
    except schema.SchemaError as e:
        logging.critical(e)
        sys.exit(__doc__)

    # setup arguments
    path = pathlib.Path(args['TRIAL'])
    dry_run = args['-x']
    verbose = True if dry_run else args['-v']
    gnu_parallel = args['--gnu-parallel']
    validate = args['--validate']

    if verbose:
        # print all info levels for user
        logging.getLogger().handlers[0].setLevel(logging.INFO)

    logging.info(f"Evaluating all patients for trial '{path}'")

    # process all encountered patients in sorted order
    for trial, patients, files in os.walk(path):
        patients.sort()

        for p_dir in patients:
            patient = Patient.from_yaml(pathlib.Path(trial).joinpath(p_dir))

            msg = f"Evaluating patient '{os.path.basename(patient.dir)}'..."
            logging.info(msg)

            if validate:
                if not patient.validate():
                    logging.critical("Failed to validate configuration file.")
                    sys.exit(1)

            # form the command; a relative path is sufficient in this case
            patient_path = path.joinpath(os.path.basename(patient.dir))
            cmd = ["patient", "run", f"{patient_path}"]

            if dry_run:
                cmd += ["-x"]

            if verbose:
                cmd += ["-v"]

            if args['--root']:
                cmd += ["--root"]

            if args['--singularity'] is not None:
                cmd += ["--singularity", args['--singularity']]

            # log the command
            logging.info(f' + isct {" ".join(cmd)}')

            if gnu_parallel:
                # write the command to `stdout` for `parallel` to read
                # assign a separate log file for each task
                logfile = patient_path.joinpath('isct.log')
                sys.stdout.write(f'isct --log {logfile} {" ".join(cmd)} \n')
                continue

            # evaluate the patient command
            patient_cmd(cmd)

        # prevent recursion of `os.walk()`
        break

    return


def trial_list(args):
    # validate run arguments
    s = schema.Schema({
        'TRIAL': schema.And(schema.Use(str), os.path.isdir),
        '--recurse': bool,
        str: object,
    })
    try:
        args = s.validate(args)
    except schema.SchemaError as e:
        logging.critical(e)
        sys.exit(__doc__)

    # setup arguments
    path = pathlib.Path(args['TRIAL'])
    recurse = args['--recurse']

    # traverse the directory
    utilities.tree(path, recurse=recurse)


def trial_status(args):
    # validate run arguments
    s = schema.Schema({
        'TRIAL': schema.And(schema.Use(str), os.path.isdir),
        str: object,
    })
    try:
        args = s.validate(args)
    except schema.SchemaError as e:
        logging.critical(e)
        sys.exit(__doc__)

    # setup arguments
    path = pathlib.Path(args['TRIAL'])

    utilities.tree(path,
                   recurse=False,
                   dir_filter=Patient.path_is_patient,
                   report=lambda p: Patient.from_yaml(p).status())


def trial_outcome(args):
    s = schema.Schema({
        'TRIAL':
        schema.And(schema.Use(str), os.path.isdir),
        '-x':
        schema.Use(bool),
        '-v':
        schema.Use(bool),
        '--singularity':
        schema.Or(None, schema.And(schema.Use(str), os.path.isdir)),
        '--root':
        schema.Use(bool),
        str:
        object,  # all other inputs do not matter
    })
    try:
        args = s.validate(args)
    except schema.SchemaError as e:
        logging.critical(e)
        sys.exit(__doc__)

    # extract variables
    path = pathlib.Path(args['TRIAL'])
    c = new_container(args['--singularity'], args['--root'])

    dry_run = True if c.dry_run() else args['-x']
    verbose = True if dry_run else args['-v']

    if verbose:
        logging.getLogger().handlers[0].setLevel(logging.INFO)

    tag = 'in-silico-trial-outcome'

    # only call into the container when its executable is present on a system
    if not c.executable_present():
        logging.critical(f"Cannot reach {c.type}.")
        return

    # exit in case the image is not present
    if not c.image_exists(tag, dry_run):
        sys.exit(1)

    # bind the trial directory
    c.bind_volume(path.absolute(), "/trial/")
    cmd = c.run_image(tag, "/trial/")

    # log command to be executed
    logging.info(" + " + " ".join(cmd))

    # evaluate the trial outcome module
    if not dry_run:
        with subprocess.Popen(cmd,
                              shell=False,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT,
                              encoding="utf-8",
                              universal_newlines=True) as proc:

            for line in iter(proc.stdout.readline, ''):
                logging.info(f'{line.strip()}\r')

    # update file permissions
    c.set_permissions(path.absolute(), tag, dry_run)


def trial_reset(args):
    s = schema.Schema({
        'TRIAL': schema.And(schema.Use(str), os.path.isdir),
        '-v': schema.Use(bool),
        str: object,  # all other inputs do not matter
    })
    try:
        args = s.validate(args)
    except schema.SchemaError as e:
        logging.critical(e)
        sys.exit(__doc__)

    # reset each patient and update its configuration file
    for patient in patients_from_trial(pathlib.Path(args['TRIAL'])):
        patient.reset()
        patient.to_yaml()


def trial(argv):
    """Provides comamnds for interaction with in-silico trials."""
    # parse command-line arguments
    args = docopt(__doc__, argv=argv)

    if args['create']:
        return trial_create(args)

    if args['outcome']:
        return trial_outcome(args)

    if args['plot']:
        return trail_plot(args)

    if args['run']:
        return trial_run(args)

    if args['reset']:
        return trial_reset(args)

    if args['status']:
        return trial_status(args)

    if args['ls']:
        return trial_list(args)


if __name__ == "__main__":
    sys.exit(trial(sys.argv[1:]))