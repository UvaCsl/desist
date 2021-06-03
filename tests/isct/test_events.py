from desist.isct.events import Events, Event

baseline = {
    'event': 'baseline',
    'models': [{'label': 'bloodflow'}, {'label': 'perfusion'}]}

stroke = {
    'event': 'stroke',
    'models': [{'label': 'place-clot'}, {'label': 'thrombectomy'}]}


def test_event():
    event = Event(baseline)
    assert event.model(0) == baseline['models'][0]
    assert event.model(1) == baseline['models'][1]
    assert event.label(0) == baseline['models'][0]['label']
    assert event.label(1) == baseline['models'][1]['label']


def test_event_models_labels():
    events = Events([baseline])
    assert list(events.labels) == ['bloodflow', 'perfusion']
    assert list(events.models) == baseline['models']


def test_events_models_labels():
    example_events = [baseline, baseline]
    events = Events(example_events)
    assert all([events[i] == example_events[i] for i in range(len(events))])
    assert list(events.labels) == ['bloodflow', 'perfusion',
                                   'bloodflow', 'perfusion']


def test_event_from_id():
    events = Events([baseline, stroke])

    assert len(events) == 2
    assert (events[0], events[1]) == (baseline, stroke)

    # event at model index
    assert events.event(0) == baseline
    assert events.event(2) == stroke

    # simulation label at model index
    assert events.label(0) == 'bloodflow'
    assert events.event(0).label(0) == 'bloodflow'
    assert events.label(2) == 'place-clot'
    assert events.event(2).label(1) == 'thrombectomy'

    assert events.model(0) == baseline['models'][0]
    assert events.model(1) == baseline['models'][1]
    assert events.model(2) == stroke['models'][0]
    assert events.model(3) == stroke['models'][1]

    # event id of a given event
    assert events.event_id(Event(baseline)) == 0
    assert events.event_id(Event(stroke)) == 1
