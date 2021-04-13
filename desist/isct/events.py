"""Helper implementation for simulation events and their models."""


class Events(list):
    """Events as a list of ``Event`` for the simulation pipeline.

    A simulation pipeline is represented by a sequence (``list``) of events
    (each of type ``Event``), each holding a set of simulation models. The
    events represent global state of the simulation phase, e.g. "baseline", or
    "treatment". Each of such events (or "states") might contain any number of
    simulation models, which are all evaluated in sequential order, i.e. by
    flattening the sequences of models per event.

    For instance, the sequence of events migth contain two stages: ``A``, and
    ``B``, where each holds ``n`` and ``m`` simulations respectively. The
    numbering is then given as ``[0, 1, 2, ..., n, n+1, n+2, ..., n+m]``.

    This class provides some helper routines to extract all events, specific
    event or model instances given a current simulation index, or to find the
    current event ID of a specific event.
    """
    def __init__(self, *args):
        list.__init__(self, *args)

    def event_id(self, event):
        """Returns the sequence index of events given an event instance."""
        return self.index(event)

    def model(self, idx):
        """Returns the model corresponding to simulation index ``idx``."""
        for (i, m) in enumerate(self.models):
            if i == idx:
                return m

    def event(self, idx):
        """Returns the event corresponding to simulation index ``idx``."""
        cnt = 0
        for event in self:
            for m in Event(event).models:
                if cnt == idx:
                    return Event(event)
                cnt += 1

    @property
    def models(self):
        """Yields all models present in all events, in flattened order."""
        for event in self:
            for m in Event(event).models:
                yield m

    def to_dict(self):
        """Returns a list of ``Events`` in their ``key:value`` dictionary."""
        return [dict(Event(event)) for event in self]


class Event(dict):
    """A simulation event represented as ``key:value`` dictionary.

    This event represents a phase in the simulation pipeline given by a
    sequence of ``Event`` by ``Events``, where each ``Event`` holds it is
    name under the ``event`` key and a list of models under ``models``.

    An event inherits from ``dict`` to provide relatively easy extensibility
    through the YAML format with additional information and keys.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def model(self, idx):
        """Returns the label of ``idx`` th model in the event."""
        models = list(self.models)
        if idx >= 0 and idx < len(models):
            return models[idx]

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
