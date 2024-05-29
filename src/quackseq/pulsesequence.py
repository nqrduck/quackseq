"""Contains the PulseSequence class that is used to store a pulse sequence and its events."""

import logging
import importlib.metadata
from collections import OrderedDict

from quackseq.pulseparameters import PulseParameter, TXPulse, RXReadout
from quackseq.functions import Function, RectFunction
from quackseq.event import Event

logger = logging.getLogger(__name__)


class PulseSequence:
    """A pulse sequence is a collection of events that are executed in a certain order.

    Args:
        name (str): The name of the pulse sequence
        version (str): The version of the pulse sequence

    Attributes:
        name (str): The name of the pulse sequence
        events (list): The events of the pulse sequence
        pulse_parameter_options (dict): The pulse parameter options
    """

    def __init__(self, name: str, version: str = None) -> None:
        """Initializes the pulse sequence."""
        self.name = name
        # Saving version to check for compatibility of saved sequence
        if version is not None:
            self.version = version
        else:
            self.version = importlib.metadata.version("quackseq")

        self.events = list()
        self.pulse_parameter_options = OrderedDict()

    def add_pulse_parameter_option(
        self, name: str, pulse_parameter_class: "PulseParameter"
    ) -> None:
        """Adds a pulse parameter option to the spectrometer.

        Args:
            name (str) : The name of the pulse parameter
            pulse_parameter_class (PulseParameter) : The pulse parameter class
        """
        self.pulse_parameter_options[name] = pulse_parameter_class

    def get_event_names(self) -> list:
        """Returns a list of the names of the events in the pulse sequence.

        Returns:
            list: The names of the events
        """
        return [event.name for event in self.events]

    def add_event(self, event: "Event") -> None:
        """Add a new event to the pulse sequence.

        Args:
            event (Event): The event to add
        """
        if event.name in self.get_event_names():
            raise ValueError(f"Event with name {event.name} already exists in the pulse sequence")
        self.events.append(event)

    def create_event(self, event_name: str, duration: str) -> "Event":
        """Create a new event and return it.

        Args:
            event_name (str): The name of the event with a unit suffix (n, u, m)
            duration (float): The duration of the event

        Returns:
            Event: The created event
        """
        event = Event(event_name, duration, self)
        if event.name in self.get_event_names():
            raise ValueError(f"Event with name {event.name} already exists in the pulse sequence")
        
        self.events.append(event)
        return event

    def delete_event(self, event_name: str) -> None:
        """Deletes an event from the pulse sequence.

        Args:
            event_name (str): The name of the event to delete
        """
        for event in self.events:
            if event.name == event_name:
                self.events.remove(event)
                break

    # Loading and saving of pulse sequences

    def to_json(self):
        """Returns a dict with all the data in the pulse sequence.

        Returns:
            dict: The dict with the sequence data
        """
        # Get the versions of this package
        data = {"name": self.name, "version": self.version, "events": []}
        for event in self.events:
            event_data = {
                "name": event.name,
                "duration": event.duration,
                "parameters": [],
            }
            for parameter in event.parameters.keys():
                event_data["parameters"].append({"name": parameter, "value": []})
                for option in event.parameters[parameter].options:
                    event_data["parameters"][-1]["value"].append(option.to_json())
            data["events"].append(event_data)
        return data

    @classmethod
    def load_sequence(cls, sequence, pulse_parameter_options):
        """Loads a pulse sequence from a dict.

        The pulse paramter options are needed to load the parameters
        and make sure the correct spectrometer is active.

        Args:
            sequence (dict): The dict with the sequence data
            pulse_parameter_options (dict): The dict with the pulse parameter options

        Returns:
            PulseSequence: The loaded pulse sequence

        Raises:
            KeyError: If the pulse parameter options are not the same as the ones in the pulse sequence
        """
        try:
            obj = cls(sequence["name"], version=sequence["version"])
        except KeyError:
            logger.error("Pulse sequence version not found")
            raise KeyError("Pulse sequence version not found")

        for event_data in sequence["events"]:
            obj.events.append(cls.Event.load_event(event_data, pulse_parameter_options))

        return obj

    # Automation of pulse sequences
    class Variable:
        """A variable is a parameter that can be used within a pulsesequence as a placeholder.

        For example the event duration a Variable with name a can be set. This variable can then be set to a list of different values.
        On execution of the pulse sequence the event duration will be set to the first value in the list.
        Then the pulse sequence will be executed with the second value of the list. This is repeated until the pulse sequence has
        been executed with all values in the list.
        """

        @property
        def name(self):
            """The name of the variable."""
            return self._name

        @name.setter
        def name(self, name: str):
            if not isinstance(name, str):
                raise TypeError("Name needs to be a string")
            self._name = name

        @property
        def values(self):
            """The values of the variable. This is a list of values that the variable can take."""
            return self._values

        @values.setter
        def values(self, values: list):
            if not isinstance(values, list):
                raise TypeError("Values needs to be a list")
            self._values = values

    class VariableGroup:
        """Variables can be grouped together.

        If we have groups a and b the pulse sequence will be executed for all combinations of variables in a and b.
        """

        @property
        def name(self):
            """The name of the variable group."""
            return self._name

        @name.setter
        def name(self, name: str):
            if not isinstance(name, str):
                raise TypeError("Name needs to be a string")
            self._name = name

        @property
        def variables(self):
            """The variables in the group. This is a list of variables."""
            return self._variables

        @variables.setter
        def variables(self, variables: list):
            if not isinstance(variables, list):
                raise TypeError("Variables needs to be a list")
            self._variables = variables


class QuackSequence(PulseSequence):
    """This is the Pulse Sequence that is compatible with all types of spectrometers.

    If you want to implement your own spectrometer specific pulse sequence, you can inherit from the PulseSequence class.
    """

    TX_PULSE = "TXPulse"
    RX_READOUT = "RXParameters"

    def __init__(self, name: str, version: str = None) -> None:
        """Initializes the pulse sequence."""
        super().__init__(name, version)

        self.add_pulse_parameter_option(self.TX_PULSE, TXPulse)
        self.add_pulse_parameter_option(self.RX_READOUT, RXReadout)

    def add_blank_event(self, event_name: str, duration: float):
        event = self.create_event(event_name, duration)

    def add_pulse_event(
        self,
        event_name: str,
        duration: float,
        amplitude: float,
        phase: float,
        shape: Function = RectFunction(),
    ):
        event = self.create_event(event_name, duration)
        self.set_tx_amplitude(event, amplitude)
        self.set_tx_phase(event, phase)
        self.set_tx_shape(event, shape)

    def add_readout_event(self, event_name: str, duration: float):
        event = self.create_event(event_name, duration)
        self.set_rx(event, True)

    # TX Specific functions

    def set_tx_amplitude(self, event, amplitude: float) -> None:
        """Sets the amplitude of the transmitter.

        Args:
            event (Event): The event to set the amplitude for
            amplitude (float): The amplitude of the transmitter
        """
        event.parameters[self.TX_PULSE].get_option_by_name(
            TXPulse.RELATIVE_AMPLITUDE
        ).value = amplitude

    def set_tx_phase(self, event, phase: float) -> None:
        """Sets the phase of the transmitter.

        Args:
            event (Event): The event to set the phase for
            phase (float): The phase of the transmitter
        """
        event.parameters[self.TX_PULSE].get_option_by_name(
            TXPulse.TX_PHASE
        ).value = phase

    def set_tx_shape(self, event, shape: Function) -> None:
        """Sets the shape of the transmitter.

        Args:
            event (Event): The event to set the shape for
            shape (Any): The shape of the transmitter
        """
        event.parameters[self.TX_PULSE].get_option_by_name(
            TXPulse.TX_PULSE_SHAPE
        ).value = shape

    # RX Specific functions

    def set_rx(self, event, rx: bool) -> None:
        """Sets the receiver on or off.

        Args:
            event (Event): The event to set the receiver for
            rx (bool): The receiver state
        """
        event.parameters[self.RX_READOUT].get_option_by_name(RXReadout.RX).value = rx
