import pytest
from click.testing import CliRunner

from desist.eventhandler.api import API
from desist.eventhandler.eventhandler import event_handler
from desist.isct.patient import Patient


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
        assert result.exit_code == 0
        assert cmd in result.output


@pytest.mark.parametrize('event_id', [0, 1])
def test_api_class(tmpdir, event_id):
    patient = Patient(tmpdir, idx=0, prefix='test')
    patient.write()

    api = TAPI(patient=patient.path, event_id=event_id)
    assert api.patient == patient
    assert api.event_id == event_id
