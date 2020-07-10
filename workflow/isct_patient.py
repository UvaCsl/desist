"""
Usage:
    isct patient create TRIAL [--id=ID] [-f] [--seed=SEED] [--config-only]

Arguments:
    TRIAL       Path to trial directory.

Options:
    -h, --help      Show this screen.
    --version       Show version.
    --id=ID         Identifier of the patient [default: 0].
    -f              Force overwrite exist patient directory.
    --seed=SEED     Random seed for the patient generation [default: 1].
    --config-only   Only generate a patient configuration file, and do not
                    invoke the `virtual_patient_generation` module.
"""

from docopt import docopt
from schema import Schema, Use, SchemaError
from pathlib import Path
from subprocess import call
import yaml
import os
import sys
import random

def create_patient_config(pid, seed):
    """Create the default patient configuration.

    Keyword arguments:
    pid -- the patient ID number (int)
    seed -- the random seed (int)
    """

    # these should be positive numbers
    assert pid >= 0
    assert seed > 0

    return {
            'id': pid,
            'status': False,
            'random_seed': seed,
    }

def add_events_to_config(config, overwrite=False):
    """Add list of events to a patient configuration.

    Keyword arguments:
    config: a dictionary represeting the patient's YAML config file.
    overwrite: bool indicate to overwrite existing events or not.
    """
    # events and their unique parameters
    # TODO: clean up this data
    # FIXME: where to obtain the default values for the time stamps

    events = [
            ("1d-blood-flow", {}),
            ("darcy_multi-comp", {"healthy": True}),
            ("cell_death_model", {
                "state": 0,
                "read_init": 0,
                "time_start": -60.0,
                "time_end": 0.0,
                }),
            ("place_clot", {"time": 0.0}),
            ("1d-blood-flow", {}),
            ("darcy_multi-comp", {}),
            ("cell_death_model", {
                "state": 1,
                "read_init": 1,
                "time_start": 0.0,
                "time_end": 18622.47003804366,
                }),
            ("thrombectomy", {}),
            ("1d-blood-flow", {}),
            ("darcy_multi-comp", {}),
            ("cell_death_model", {
                "state": 2,
                "read_init": 2,
                "time_start": 18622.47003804366,
                "time_end": 22222.47003804366,
                }),
            ("patient_outcome", {}),
    ]

    # ensure we do not overwrite existing event specifications
    if 'events' in config and not overwrite:
        pid = config['id'] if 'id' in config else -1
        pname = config['name'] if 'name' in config else "unknown"
        msg = f"Patient: 'id: {pid}, name: {pname}' already contains events.\n"
        msg += "Provide '-f' to overwrite"
        sys.exit(msg)
        return

    # initialise events to empty list
    config['events'] = []

    # store length of pipeline
    config['pipeline_length'] = len(events)

    # build the list of events with settings
    for i, (event, settings) in enumerate(events):
        defaults = {
                'event': event,
                'id': i,
                'status': False,
        }

        # append event and merge its defaults with specific settings
        config['events'] += [{**defaults, **settings}]

    return config

def config_yaml_to_xml(config):
    """Converts a patient's configuration into XML ElementTree.

    This function mainly exists to convert the YAML format into XML to match the
    previous definition of the configuration files. The function returns an
    `xml.etree.ElementTree` form of the config file.

    Keyword arguments:
    config: dictionary obtained by loading the patient's YAML config file
    """

    import xml.etree.ElementTree as ET

    # basic setup
    root = ET.Element("virtualPatient")
    patient = ET.SubElement(root, "Patient")

    # Directly convert each (key, value) into an XML element, except for the
    # events. These are given as a list and require specific treament.
    for key, val in config.items():

        # directly convert the key to XML element with text set to its value
        if key != 'events':
            el = ET.SubElement(patient, key)
            el.text = str(val)
            continue

        # adds the <events> element
        events = ET.SubElement(patient, key)

        # adds an <event> element for each event
        for event in config['events']:
            e = ET.SubElement(events, "event")

            # Each (key, value) of settings per event are now converted to
            # attributes of the XML document. Note, "event" is converted into
            # "name" to match the original format
            for k, v in event.items():
                if k == "event":
                    e.set("name", str(v))
                else:
                    e.set(k, str(v))

    # return the full XML root
    return root

def patient(argv):
    """Provides commands for interaction with virtual patients."""
    # parse command-line arguments
    args = docopt(__doc__, argv=argv)

    # schema for argument validation
    schema = Schema(
            {
                '--id': Use(int, error='Only integer patient ID allowed'),
                '--seed': Use(int, error='Only integer random seeds allowed'),
                str: object,
                }
            )

    # validate arguments
    try:
        args = schema.validate(args)
    except SchemaError as e:
        print(e)
        sys.exit(__doc__)

    # find the configuration file
    path = Path(args['TRIAL'])
    yml = path.joinpath("trial.yml")
    patient_id = args['--id']
    overwrite = args['-f']
    seed = args['--seed']

    # ensure configuration file exists
    if not os.path.isfile(yml):
        sys.exit(f"No trial configuration is found in '{path}'")

    # load trial configuration
    with open(yml, "r") as outfile:
        trial_config = yaml.load(outfile, yaml.SafeLoader)

    # construct patient directory
    patient_prefix = trial_config['prefix']
    patient_postfix = f"{patient_id:03}"
    patient = path.joinpath(f"{patient_prefix}_{patient_postfix}")

    # require explicit -f to overwrite existing patient directories
    if os.path.isdir(patient) and not overwrite:
        print(f"Patient '{patient}' already exist. Provide -f to overwrite")
        sys.exit(__doc__)

    # clear out old, existing path
    if os.path.isdir(patient):
        import shutil
        shutil.rmtree(patient)

    # setup patient directory and fill
    os.makedirs(patient, exist_ok=True)

    # seed the random generator with the provided seed
    random.seed(seed)

    # pull the n-th random number, for the n-th patient
    for i in range(patient_id+1):
       p_seed = random.randrange(2<<31 - 1)

    # setup a basic configuration, to be filled by `virtual_patient_generation`
    config = create_patient_config(patient_id, p_seed)

    # write patient configuration to disk
    config_path = patient.joinpath("patient.yml")

    with open(config_path, "w") as outfile:
        yaml.dump(config, outfile)

    # only call docker to fill the patients data when not set
    if not args['--config-only']:
        cmd = [
                "docker",
                "run", "-v", f"{path.absolute()}:/patients/",
                "virtual_patient_generation",
                f"/patients/{patient_prefix}_{patient_postfix}"
        ]

        # only call into Docker when available on the system
        if shutil.which("docker") is None:
            print("Cannot reach Docker.")
            return

        call(cmd)

    # events are added _after_ `virtrual_patient_generation` to allow for the
    # possibility of adding logic in the events, e.g. if age > criteria then
    # assume a different event chain

    # read the config back
    with open(config_path, "r") as configfile:
        config = yaml.load(configfile, yaml.SafeLoader)

    # add the events
    config = add_events_to_config(config, overwrite)

    # clear file and write back updated configuration
    with open(config_path, "w") as outfile:
        yaml.dump(config, outfile)

    # FIXME: convert YAML to XML should not be required as we move towards YAML
    config_xml = config_yaml_to_xml(config)

    # `xml.tree.ElementTree` for dumping config_xml
    # `xml.dom.minidom` for making it somewhat human readable (ident, etc.)
    import xml.etree.ElementTree as ET
    import xml.dom.minidom
    with open(patient.joinpath("config.xml"), "w") as outfile:
        xml_string = ET.tostring(config_xml, encoding="unicode")
        dom = xml.dom.minidom.parseString(xml_string)
        outfile.write(dom.toprettyxml())

if __name__ == "__main__":
    sys.exit(patient(sys.argv[1:]))
