import os
import pathlib
import yaml
import sys

import workflow.utilities as utilities

class Patient(dict):
    """Representation of a patient."""

    def __init__(self, path, *args, **kwargs):
        """Initialise a patient like a dictionary."""

        # path to the directory containing the patient
        self.dir = pathlib.Path(str(path)).absolute()

        # filename of the configuration file, this goes into self.path/
        self.filename = "patient.yml"

        self.update(*args, **kwargs)

    def __repr__(self):
        dictrepr = dict.__repr__(self)
        return f"{type(self).__name__}({dict.__repr__(self)})"

    def update(self, *args, **kwargs):
        """Update the value within the Patient's dictionary."""
        for k, v in dict(*args, **kwargs).items():
            self[k] = v

    @classmethod
    def from_yaml(cls, yaml_path):
        """Create a Patient from a YAML configuration file."""

        # if a directory is provided, append default config filename
        yaml_path = pathlib.Path(yaml_path)
        if os.path.isdir(yaml_path):
            yaml_path = yaml_path.joinpath("patient.yml")

        with open(yaml_path, "r") as configfile:
            config = yaml.load(configfile, yaml.SafeLoader)

        # split filename from directories' path
        path, _ = os.path.split(os.path.normpath(yaml_path))
        return cls(path, **config)

    def to_yaml(self):
        """Dumps the Patient configuration towards a yaml file on disk."""
        with open(self.dir.joinpath(self.filename), "w") as outfile:
            yaml.dump(dict(self), outfile)

    def to_xml(self):
        """Dumps the Patient configuration dictionary towards xml file."""
        # dictionary to xml conversion
        xml_config = dict_to_xml(dict(self))

        # prettify output
        import xml.etree.ElementTree as ET
        import xml.dom.minidom
        with open(self.dir.joinpath("config.xml"), "w") as outfile:
            xml_str = ET.tostring(xml_config, encoding="unicode")
            dom = xml.dom.minidom.parseString(xml_str)
            outfile.write(dom.toprettyxml())

    def full_path(self):
        return self.dir.joinpath(self.filename).absolute()

    def set_defaults(self, pid, seed):
        """Insert default configuration into the current patient.

        Keyword arguments:
        pid -- the patient ID number (int)
        seed -- the random seed for the patient (int)
        """

        assert type(pid) == int and pid >= 0
        assert type(seed) == int and seed >= 0

        git_sha = utilities.get_git_hash(utilities.isct_module_path())
        if git_sha == "":
            git_sha = "not_found"

        defaults = {
            'git_sha': git_sha,
            'id': pid,
            'status': False,
            'random_seed': seed,
            'HeartRate': 60,
            'SystolePressure': 17300,
            'DiastolePressure': 10100,
            'MeanRightAtrialPressure': 0,
            'StrokeVolume': 70,
        }

        self.update(**defaults)
        return self

    def set_events(self, overwrite=False):
        """Add list of events to a patient configuration.

        Keyword arguments:
        overwrite: bool indicate to overwrite existing events or not.
        """

        # do not modify the already existing events
        if len(self.events()) > 0:
            msg = f"Events already exist, while overwrite is {overwrite}"
            assert overwrite, msg

        # FIXME where to obtain default values?
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
                ("patient-outcome-model", {}),
        ]

        # initialise events to empty list
        self['events'] = []

        # store length of pipeline
        self['pipeline_length'] = len(events)

        # build the list of events with settings
        for i, (event, settings) in enumerate(events):
            defaults = {
                    'event': event,
                    'id': i,
                    'status': False,
            }

            # append event and merge its defaults with specific settings
            self['events'] += [{**defaults, **settings}]

        return self

    def events(self):
        """Returns a list of events of the current patient."""
        return self.get('events', [])

    def status(self):
        """Returns a string indicating the event status: o: True, x: False."""
        status = ["o" if event['status'] else "x" for event in self.events()]
        status = " ".join(status)
        return f" [ {status} ]"

def dict_to_xml(config):
    """Helper routine to convert a dictionary towards a XML formation."""
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

