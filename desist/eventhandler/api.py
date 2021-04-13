import abc

from desist.isct.patient import Patient


class API(abc.ABC):
    def __init__(self, patient, event_id):
        self.patient = Patient.read(patient)
        self.event_id = event_id

    @abc.abstractmethod
    def event(self):
        """Abstract event implementation"""

    @abc.abstractmethod
    def example(self):
        """Abstract example implementation"""

    @abc.abstractmethod
    def test(self):
        """Abstract test implementation"""
