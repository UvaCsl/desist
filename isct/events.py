# FIXME: write separate documentation page on format of events/models
# FIXME: improve documentation
class Events(list):
    """Events contains a list of events for the simulation pipeline.

    Should support:
    - simply conversion to `dict`
    - listing of all available events for the pipeline

    """
    def __init__(self, *args):
        list.__init__(self, *args)

    @property
    def models(self):
        for event in self:
            for m in Event(event).models:
                yield m

    def to_dict(self):
        return [dict(Event(event)) for event in self]


# FIXME: improve documentation
class Event(dict):
    """Event represents a dictionary of labels and models.
    - FIXME: improve doc
    - listing of all present models
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def models(self):
        for model in self.get('models'):
            yield model.get('label')


# FIXME: support external definitions of the list of events:
# These events are now hardcoded for the INSIST project. Prefrably these are
# read from an additional argument passed into the `trial create` commands.

# FIXME: insert the label mapping from label -> container name? Unclear if this
# is strictly needed

# FIXME: insert a `occlusion_to_vessel` map in the virtual patient model
# FIXME: insert a `left_vs_right` sampling step in the virtual patient model
# FIXME: add temporary support to export from YAML to XML...

baseline_event = Event({
    'event':
    'baseline',
    'models': [{
        'label': '1d-blood-flow',
    }, {
        'label': 'perfusion_and_tissue_damage',
        'type': 'PERFUSION'
    }, {
        'label': 'perfusion_and_tissue_damage',
        'type': 'OXYGEN'
    }]
})

stroke_event = Event({
    'event':
    'stroke',
    'models': [{
        'label': 'place_clot',
    }, {
        'label': '1d-blood-flow',
    }, {
        'label': 'perfusion_and_tissue_damage',
        'type': 'PERFUSION'
    }, {
        'label': 'perfusion_and_tissue_damage',
        'type': 'OXYGEN'
    }]
})

treatment_event = Event({
    'event':
    'treatment',
    'models': [{
        'label': 'thrombectomy',
    }, {
        'label': '1d-blood-flow',
    }, {
        'label': 'perfusion_and_tissue_damage',
        'type': 'PERFUSION'
    }, {
        'label': 'perfusion_and_tissue_damage',
        'type': 'OXYGEN'
    }, {
        'label': 'patient-outcome-model'
    }]
})

# FIXME: add the patient-outcome model to the end of events
default_events = Events([baseline_event, stroke_event, treatment_event])

# FIXME: the labels should also be inserted externally
default_labels = {k: k.replace("_", "-") for k in default_events.models}
