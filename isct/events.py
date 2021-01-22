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


# FIXME: support for _external_ definition of patient / event pipeline
example_event = Event({
    'event': 'baseline',
    'models': [{
        'label': 'place-clot'
    }, {
        'label': 'place-clot'
    }]
})

default_events = Events([example_event, example_event])
