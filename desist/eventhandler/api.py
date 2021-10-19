"""Abstract API definition for ``desist`` pipelines."""

import abc
import os

from desist.isct.patient import Patient


class API(abc.ABC):
    """Abstract API implementation for event handling in ``desist``.

    This provides an abstract API implementation to link various simulation
    events within a simulation pipeline. The API provides the entry point
    where each simulation is accessed and is initialised with the path to the
    current patient and the index of the current (to be evaluated) model.

    The user is then required to provide the implementation of three methods:
    ``event``, ``example``, and ``test``. The latter two are intended for
    example and testing routines, whereas the ``event`` call is the intended
    call to evaluate the simulation of the pipeline.

    Typically, only a single call is required to dispatch towards the
    current simulation, e.g. using the ``subprocess`` library by invoking
    a call to the current simulation ``subprocess.run(["program", "args"])``.
    However, the abstract API implementation provides a number of helper
    routines to simplify additional operations, e.g. ``current_event``,
    ``next_event``, ``previous_event``, and ``result_dir``, to easily
    locate simulation files of current/previous events and the corresponding
    default output locations.
    """
    def __init__(self, patient, model_id):
        self.patient = Patient.read(patient)
        self.model_id = model_id
        self.event_id = self.events.event_id(self.current_event)

        # ensure output directory is present on the system
        if not os.path.isdir(self.result_dir):
            os.makedirs(self.result_dir)

    @property
    def events(self):
        """Returns all events of the simulation as ``Events`` instance."""
        return self.patient.events

    # TODO: consider adding a `labels` property as well

    @property
    def current_event(self):
        """The current event corresponding to ``self.model_id``."""
        return self.events.event(self.model_id)

    @property
    def next_event(self):
        """The next event with respect to the ``self.model_id``.

        Returns ``None`` if no subsequent event is present.
        """
        if (eid := self.event_id + 1) < len(self.events):
            return self.events[eid]

    @property
    def previous_event(self):
        """The previous event with respect to the ``self.model_id``.

        Returns ``None`` if no previous event is present.
        """
        if (eid := self.event_id - 1) >= 0:
            return self.events[eid]

    @property
    def current_model(self):
        """Return the current model definition from the list of events."""
        return self.events.model(self.model_id)

    @property
    def current_label(self):
        """Returns the current label of the list of events."""
        return self.events.label(self.model_id)

    @property
    def patient_dir(self):
        """This points to the current patient directory."""
        return self.patient.dir

    @property
    def result_dir(self):
        """The output directory for the results of the current event."""
        return self.patient.dir.joinpath(self.current_event.get('event'))

    @property
    def previous_result_dir(self):
        """The output directory for the previous event.

        Returns ``None`` if no previous event is present.
        """
        if self.previous_event is None:
            return None

        return self.patient.dir.joinpath(self.previous_event.get('event'))

    @abc.abstractmethod
    def event(self):
        """Abstract event implementation."""

    @abc.abstractmethod
    def example(self):
        """Abstract example implementation."""

    @abc.abstractmethod
    def test(self):
        """Abstract test implementation."""
