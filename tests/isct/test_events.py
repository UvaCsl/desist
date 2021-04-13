from desist.isct.events import Events, Event

baseline = {
    'event': 'baseline',
    'models': [{'label': 'bloodflow'}, {'label': 'perfusion'}]}

stroke = {
    'event': 'stroke',
    'models': [{'label': 'place-clot'}, {'label': 'thrombectomy'}]}


def test_event_models():
    events = Events([baseline])
    assert list(events.models) == ['bloodflow', 'perfusion']


def test_events_models():
    example_events = [baseline, baseline]
    events = Events(example_events)
    assert all([events[i] == example_events[i] for i in range(len(events))])
    assert list(events.models) == ['bloodflow', 'perfusion',
                                   'bloodflow', 'perfusion']


def test_event_from_id():
    events = Events([baseline, stroke])

    assert len(events) == 2
    assert (events[0], events[1]) == (baseline, stroke)

    # event at model index
    assert events.event(0) == baseline
    assert events.event(2) == stroke

    # simulation label at model index
    assert events.model(0) == 'bloodflow'
    assert events.event(0).model(0) == 'bloodflow'
    assert events.model(2) == 'place-clot'
    assert events.event(2).model(1) == 'thrombectomy'

    # event id of a given event
    assert events.event_id(Event(baseline)) == 0
    assert events.event_id(Event(stroke)) == 1

