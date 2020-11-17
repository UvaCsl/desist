import enum
import os
import pathlib
import random
import schema
import yaml

from . import utilities


@enum.unique
class Event(enum.IntEnum):
    """Enumerated type indicating the event of the trial.

    The event of the trial is used to determine the placement of output during
    the trial. The values of the enumerated type correspond to the relative
    directories inside the `/patient/` directory where the results will be
    stored.
    """
    BASELINE = 0
    STROKE = 1
    TREATMENT = 2

    @staticmethod
    def from_str(label):
        for event in Event:
            if label.lower() == event.name.lower():
                return event

    @staticmethod
    def validate_event(event):
        if isinstance(event, str):
            return Event._validate_string(event)
        if isinstance(event, int):
            return Event._validate_integer(event)

    @staticmethod
    def _validate_string(event):
        return Event.from_str(event) is not None

    @staticmethod
    def _validate_integer(event):
        return event in Event.__members__.values()


class Model(enum.Enum):
    BLOODFLOW = "1d-blood-flow"
    PERFUSION = "perfusion_and_tissue_damage"
    OXYGEN = "perfusion_and_tissue_damage"
    TISSUE_DAMAGE = "tissue_damage"
    PLACE_CLOT = "place_clot"
    THROMBECTOMY = "thrombectomy"
    THROMBOLYSIS = "thrombolysis"
    PATIENT_OUTCOME = "patient-outcome-model"

    @staticmethod
    def from_str(label):
        for model in Model:
            if label == model.value:
                return model

    @staticmethod
    def from_name(name):
        for model in Model:
            if name == model.name:
                return model

    @staticmethod
    def parse_models(models):
        return list(filter(Model.from_str, models))

    @staticmethod
    def validate_models(models):
        models = [models] if not isinstance(models, list) else models
        return len(models) == len(Model.parse_models(models))


def patients_from_trial(trial):
    """Returns all patient instances in the given trial directory."""
    trial = pathlib.Path(trial)
    assert os.path.isdir(trial)

    return map(Patient.from_yaml,
               filter(lambda p: os.path.isdir(p), trial.iterdir()))


class Patient(dict):
    """Representation of a patient."""
    def __init__(self, path, *args, **kwargs):
        """Initialise a patient like a dictionary."""

        # path to the directory containing the patient
        self.dir = pathlib.Path(str(path)).absolute()

        # filename of the configuration file, this goes into self.path/
        self.filename = "patient.yml"

        # complete path of the patient
        self.path = self.dir.joinpath(self.filename)

        # insert the keys in the dict
        self.update(*args, **kwargs)

    def __repr__(self):
        return f"{type(self).__name__}({dict.__repr__(self)})"

    @property
    def terminated(self):
        """Returns true if the simulation should terminate."""
        if 'terminated' not in dict(self):
            return False
        return self['terminated']

    @terminated.setter
    def terminated(self, value):
        self['terminated'] = value

    def terminate(self):
        self.terminated = True

    def reset(self):
        """Resets the status of the patient.

        Currently only resets the `terminated` flag.
        """

        if 'terminated' in dict(self):
            del self['terminated']

    def validate(self):
        """Returns True if the patient config is validated sucessfully.

        For variables which have explicit types, i.e. name has to be a string,
        the schema enforces this by assertig `str`, while for variables that
        should end up as float or int, we just cast to the corresponding type
        using `schema.Use(...)`. Additionally, the schema will enforce any
        variables that are limited to an a priori known set to be limited to
        that set. Finally, most parameters are bound to either positive
        `n >= 0` or bigger positive and non-zero `n > 0`.

        The events are validated separately. When evaluating the complete
        config, it only concers with the presence of the keys `id`, `event`,
        and `status`. Later, each event is validated individually to constrain
        these keys to allowed values. Any other parameters are not enforced at
        this moment, as it is not clearly known what their constraints are.
        """

        s = schema.Schema({
            'models': [
                schema.And(
                    lambda e: all([b in e for b in ["id", "model", "status"]]))
            ],
            'ASPECTS_BL':
            schema.And(float, lambda n: n > 0),
            'DiastolePressure':
            schema.And(schema.Use(float), lambda n: n > 0),
            'HeartRate':
            schema.And(schema.Use(float), lambda n: n > 0),
            'MeanRightAtrialPressure':
            schema.Use(float),
            'NIHSS_BL':
            schema.And(float, lambda n: n > 0),
            'StrokeVolume':
            schema.Use(float),
            'SystolePressure':
            schema.Use(float),
            'age':
            schema.And(float, lambda n: n > 0),
            'collaterals':
            schema.Use(float),
            'dur_oer':
            schema.Use(float),
            'er_iat_groin':
            schema.Use(float),
            'git_sha':
            str,
            'id':
            schema.And(int, lambda n: n >= 0),
            'name':
            str,
            'occlsegment_c_short':
            schema.Use(float),
            'pipeline_length':
            schema.And(int, lambda n: n > 0),
            'premrs':
            schema.Use(float),
            'prev_af':
            schema.Use(float),
            'prev_dm':
            schema.Use(float),
            'prev_str':
            schema.Use(float),
            'random_seed':
            schema.And(int, lambda n: n > 0),
            'rr_syst':
            schema.Use(float),
            'sex':
            schema.And(float, lambda s: int(s) == 0 or int(s) == 1),
            'sex_long':
            schema.And(str, schema.Use(str.lower), lambda s: s in
                       ('male', 'female')),
            'status':
            bool,
        })

        try:
            s.validate(dict(self))
        except schema.SchemaError as e:
            print(f"Validation failed with error `{e}`")
            return False

        # parse model properties individually
        s = schema.Schema({
            'id':
            schema.And(int, lambda n: n >= 0),
            'status':
            bool,
            'model':
            schema.And(str, schema.Use(str.lower),
                       lambda s: Model.validate_models(s)),
            schema.Optional(str):
            object,
        })
        for model in dict(self)['models']:
            try:
                s.validate(model)
            except schema.SchemaError as e:
                print(f"Validation failed with error `{e}`")
                return False

        return True

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

        # extract configuration from file
        config = utilities.read_yaml(yaml_path)

        # split filename from directories' path
        path, _ = os.path.split(os.path.normpath(yaml_path))
        return cls(path, **config)

    def to_yaml(self):
        """Dumps the Patient configuration towards a yaml file on disk."""
        with open(self.dir.joinpath(self.filename), "w") as outfile:
            yaml.dump(dict(self), outfile)

        return self

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

        return self

    def full_path(self):
        return self.dir.joinpath(self.filename).absolute()

    def update_defaults(self):
        # Translate variable name from `virtual patient generation` towards the
        # blood flow (and subsequent) models.
        if 'rr_syst' in self:
            self['SystolePressure'] = self['rr_syst']

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
            'DiastolePressure': 10100,
            'MeanRightAtrialPressure': 0,
            'StrokeVolume': 70,
        }

        self.update(**defaults)
        return self

    def create_default_files(self):
        """Initialises default files in patient directory."""

        # integer to string mapping for occlusion segment
        occlusion_to_vessel = {
            0: 'M2',  # originally M3, mapped to M2 for anatomy model
            1: 'IICA',  # L/R
            2: 'ICAT',  # L/R
            3: 'M1',  # L/R
            4: 'M2',  # 4 locations (2 defs + L/R) - just pick randomly
        }

        # mapping from virtual patient model towards anatomy definition in
        # one-dimensional blood flow analysis
        # FIXME: mapping to be updated
        vessel_to_anatomy = {
            'M1': 'MCA',
            'M2': 'MCA',
            'IICA': 'MCA',
            'ICAT': 'MCA',
        }

        # convert occlusion segment into blood-flow vessel name
        occlusion_id = int(self.get('occlsegment_c_short', 0))
        segment = vessel_to_anatomy[occlusion_to_vessel[occlusion_id]]

        # left or right side: about 50/50 choice
        # FIXME: to be updated with improved distributions
        left_or_right = random.choice(("L", "R"))
        vessel = f'"{left_or_right}. {segment}"'

        # `Clots.txt` layed out as list of tuples
        data = [("Vesselname", vessel), ("Clotlocation(mm)", 3),
                ("Clotlength(mm)", 15), ("Permeability", 0), ("Porosity", 0)]

        # Write data to file as csv (header separated by `,` values by `\t`
        with open(self.dir.joinpath("Clots.txt"), "w") as outfile:
            header = ",".join([d[0] for d in data])
            outfile.write(header)
            outfile.write('\n')
            clot = ",".join([str(d[1]) for d in data])
            outfile.write(clot)

    def event(self, model_id):
        """The event corresponding to the ith model (model_id)."""
        model = self.get_model(model_id)
        if model is None:
            return ''
        return model['event']

    def event_id(self, model_id):
        """The ID of the current event."""
        model = self.get_model(model_id)
        if model is None:
            return 0
        return model['event_id']

    def event_from_id(self, event_id):
        """The event corresponding to the ith event (event_id)."""
        event = next(x for i, x in enumerate(self.events) if i == event_id)
        return event['event']

    @property
    def events(self):
        """Generator for all events present in the configuration."""
        for event in self.get('events', []):
            yield event

    @property
    def models(self):
        """Generator for all models present in the configuration.

        This injects the corresponding event's `event`, `event_id` keys into
        the current model. This simplifies accessing these properties in
        subclass implementations. Also, when a list of `labels` is present
        in the patient configruation (these map the model names towards
        corresponding container labels/tags), the mapping is evaluate and added
        to the model dictionary under the `container` key.
        """
        labels = self.get('labels', None)
        for i, event in enumerate(self.events):
            for model in event['models']:
                augment = {'event': event['event'], 'event_id': i}
                if labels:
                    augment['container'] = labels[model['label']]
                yield {**model, **augment}

    def get_model(self, model_id):
        """Dictionary of the model with ID `model_id`."""
        return next((x for i, x in enumerate(self.models) if i == model_id),
                    None)

    def set_models(self, overwrite=False):
        """Add list of events to a patient configuration.

        Keyword arguments:
        overwrite: bool indicate to overwrite existing events or not.

        TODO:
        Extract timestamps of events, or assign defaults when not present.
        These give the time between onset and arrival at ER `onset_to_er`
        and the time from ER arrival to groin punction `er_iat_groin`. The
        elapsed time after the complete procedure is the sum of both. The
        `baseline` simulation is set at one hour (-60 min) in the timeline to
        indicate it happens before the stroke event.
        onset_to_er = self.get('dur_oer', 86.60659896539732)
        er_to_puncture = self.get('er_iat_groin', 77.00683786676517)
        """

        # do not modify the already existing events
        if len(list(self.models)) > 0:
            msg = f"Models already exist, while overwrite is {overwrite}"
            assert overwrite, msg

        self['labels'] = {m.name.lower(): m.value for m in Model}
        self['events'] = []
        self['completed'] = -1

        # todo this can be changed by default dict..
        for i, e in enumerate(Event):
            if e == Event.BASELINE:
                event = {
                    'event':
                    e.name.lower(),
                    'models': [
                        {
                            'label': Model.BLOODFLOW.name
                        },
                        {
                            'label': Model.PERFUSION.name,
                            'type': 'PERFUSION'
                        },
                        {
                            'label': Model.OXYGEN.name,
                            'type': 'OXYGEN'
                        },
                    ]
                }

            if e == Event.STROKE:
                event = {
                    'event':
                    e.name.lower(),
                    'models': [
                        {
                            'label': Model.PLACE_CLOT.name
                        },
                        {
                            'label': Model.BLOODFLOW.name
                        },
                        {
                            'label': Model.PERFUSION.name,
                            'type': 'PERFUSION'
                        },
                        {
                            'label': Model.OXYGEN.name,
                            'type': 'OXYGEN'
                        },
                    ]
                }

            if e == Event.TREATMENT:
                event = {
                    'event':
                    e.name.lower(),
                    'models': [
                        {
                            'label': Model.THROMBECTOMY.name
                        },
                        {
                            'label': Model.BLOODFLOW.name
                        },
                        {
                            'label': Model.PERFUSION.name,
                            'type': 'PERFUSION',
                            'evaluate_infarct_estimates': True,
                        },
                        {
                            'label': Model.OXYGEN.name,
                            'type': 'OXYGEN'
                        },
                        {
                            'label': Model.PATIENT_OUTCOME.name
                        },
                    ]
                }

            for model in event['models']:
                model['label'] = model['label'].lower()

            self['events'].append(event)

        # store length of pipeline
        self['pipeline_length'] = sum([len(e['models']) for e in self.events])

        return self

    def match_tag_id(self, tag, model_id):
        for mid, model in enumerate(self.models):
            if model.get('container', '') == tag and mid == model_id:
                return True
        return False

    def status(self):
        """Returns a string indicating the model status: o: True, x: False."""
        if self['completed'] < 0:
            status = ["x" for model in self.models]
            status = " ".join(status)
            return f" [ {status} ]"

        status = []
        for mid, _ in enumerate(self.models):
            if mid > self['completed']:
                mark = "x"
            else:
                mark = "o"
            status.append(mark)

        status = " ".join(status)
        return f" [ {status} ]"

    def completed_model(self, model_id):
        """Marks the status of model with id = `model_id` to True."""
        for mid, model in enumerate(self.models):
            if mid == model_id:
                self['completed'] = mid
                return

    @staticmethod
    def path_is_patient(path):
        """True if the path contains a non-empty patient configuration file."""
        path = pathlib.Path(path).joinpath("patient.yml")
        if not path.is_file():
            return False
        return utilities.read_yaml(path) != {}


def dict_to_xml(config):
    """Helper routine to convert a dictionary towards a XML formation."""
    import xml.etree.ElementTree as ET

    # basic setup
    root = ET.Element("virtualPatient")
    patient = ET.SubElement(root, "Patient")

    # Directly convert each (key, value) into an XML element, except for the
    # events. These are given as a list and require specific treament.
    for key, val in config.items():

        if key == 'models' or key == 'events':
            continue

        # directly convert the key to XML element with text set to its value
        el = ET.SubElement(patient, key)
        el.text = str(val)

    return root
