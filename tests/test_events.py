from desist.isct.events import Events, Event

example_event = {
    'event': 'baseline',
    'models': [{
        'label': 'bloodflow'
    }, {
        'label': 'perfusion'
    }]
}

example_events = [example_event, example_event]


def test_event_models():
    event = Event(example_event)
    assert event == example_event
    assert list(event.models) == ['bloodflow', 'perfusion']


def test_events_models():
    events = Events(example_events)
    assert all([events[i] == example_events[i] for i in range(len(events))])
    assert list(events.models) == ['bloodflow', 'perfusion',
                                   'bloodflow', 'perfusion']
