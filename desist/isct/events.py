"""Helper implementation for simulation events and their models."""


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
        """Yield the models present all events."""
        for event in self:
            for m in Event(event).models:
                yield m

    def to_dict(self):
        """Convert a list of ``Events`` into a ``key:value`` dictionary."""
        return [dict(Event(event)) for event in self]


# FIXME: improve documentation
class Event(dict):
    """An event represented as key:value dictionary of labels and models."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def models(self):
        """Yield the labels of the available models in the current event."""
        for model in self.get('models'):
            yield model.get('label')


# FIXME: support external definitions of the list of events:
# These events are now hardcoded for the INSIST project. Prefrably these are
# read from an additional argument passed into the `trial create` commands.

baseline_event = Event({
    'event':
    'baseline',
    'models': [{
        'label': '1d-blood-flow',
    }, {
        'label': 'perfusion_and_tissue_damage',
        'type': 'PERFUSION'
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
        'evaluate_infarct_estimates': True,
        'label': 'perfusion_and_tissue_damage',
        'type': 'PERFUSION'
    }, {
        'label': 'patient-outcome-model'
    }]
})

default_events = Events([baseline_event, stroke_event, treatment_event])
default_labels = {k: k.replace("_", "-") for k in default_events.models}
