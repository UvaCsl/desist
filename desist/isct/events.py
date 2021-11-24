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

    def label(self, idx):
        """Returns the label corresponding to simulation index ``idx``."""
        for (i, label) in enumerate(self.labels):
            if i == idx:
                return label

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

    @property
    def labels(self):
        """Yields all labels present in all events, in flattened order."""
        for event in self:
            for label in Event(event).labels:
                yield label

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
        """Returns the label of the ``idx``th model in the event."""
        models = list(self.models)
        if idx >= 0 and idx < len(models):
            return models[idx]

    def label(self, idx):
        """Returns the label of the ``idx``th label in the event."""
        labels = list(self.labels)
        if idx >= 0 and idx < len(labels):
            return labels[idx]

    @property
    def models(self):
        """Yield all models available in the current event."""
        for model in self.get('models'):
            yield model

    @property
    def labels(self):
        """Yields all labels available in the current event."""
        for label in map(lambda x: x.get('label'), self.models):
            yield label
