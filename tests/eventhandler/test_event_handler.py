import pytest
from click.testing import CliRunner

from desist.eventhandler.api import API
from desist.eventhandler.eventhandler import event_handler
from desist.isct.patient import Patient
from desist.isct.events import baseline_event, stroke_event, treatment_event


class TAPI(API):
    """Test class to ensure API calls are forwarded to defined functions."""
    def event(self):
        print('event')

    def example(self):
        print('example')

    def test(self):
        print('test')


def test_eventhandler_noop():
    runner = CliRunner()
    with runner.isolated_filesystem():
        # no args
        result = runner.invoke(event_handler())
        assert result.exit_code == 0

        # missing args
        result = runner.invoke(event_handler(), [])
        assert result.exit_code == 0


@pytest.mark.parametrize('cmd', ['event', 'example', 'test'])
def test_eventhandler(tmpdir, cmd):
    runner = CliRunner()
    patient = Patient(tmpdir, idx=0, prefix='test')
    path = patient.path

    with runner.isolated_filesystem():

        result = runner.invoke(event_handler(), [str(path), 0])
        assert result.exit_code == 2
        assert 'does not exist' in result.output

        patient.write()

        result = runner.invoke(event_handler(TAPI), [str(path), 0, cmd])
        print(result.output)
        assert result.exit_code == 0
        assert cmd in result.output


@pytest.mark.parametrize('model_id', [0, 1])
def test_api_class(tmpdir, model_id):
    patient = Patient(tmpdir, idx=0, prefix='test')
    patient.write()

    api = TAPI(patient=patient.path, model_id=model_id)
    assert api.patient == patient
    assert api.model_id == model_id
    assert api.patient_dir == patient.path.parent
    assert api.current_label == patient.events.label(model_id)
    assert api.current_model == patient.events.model(model_id)


def test_api_helpers(tmpdir):
    patient = Patient(tmpdir, idx=0, prefix='test')
    patient.write()

    api = TAPI(patient=patient.path, model_id=0)
    assert api.previous_event is None
    assert api.current_event == baseline_event
    assert api.next_event == stroke_event
    assert api.previous_result_dir is None

    n_models = len(list(patient.events.models)) - 1
    api = TAPI(patient=patient.path, model_id=n_models)
    assert api.previous_event == stroke_event
    assert api.current_event == treatment_event
    assert api.next_event is None
    assert api.previous_result_dir.parent == patient.dir
