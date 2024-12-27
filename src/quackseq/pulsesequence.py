"""Contains the PulseSequence class that is used to store a pulse sequence and its events."""

import logging
import importlib.metadata
from collections import OrderedDict

from quackseq.pulseparameters import PulseParameter, TXPulse, RXReadout
from quackseq.functions import Function, RectFunction
from quackseq.event import Event
from quackseq.phase_table import PhaseTable

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
            raise ValueError(
                f"Event with name {event.name} already exists in the pulse sequence"
            )

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
            raise ValueError(
                f"Event with name {event.name} already exists in the pulse sequence"
            )
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

    def get_event_by_name(self, event_name: str) -> "Event":
        """Returns an event by name.

        Args:
            event_name (str): The name of the event

        Returns:
            Event: The event with the name
        """
        for event in self.events:
            if event.name == event_name:
                return event

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
    def load_sequence(cls, sequence):
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
            event = Event.load_event(event_data, obj)
            obj.events.append(event)

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

    TX_PULSE = "TX"
    RX_READOUT = "RX"

    def __init__(self, name: str, version: str = None) -> None:
        """Initializes the pulse sequence."""
        super().__init__(name, version)

        self.add_pulse_parameter_option(self.TX_PULSE, TXPulse)
        self.add_pulse_parameter_option(self.RX_READOUT, RXReadout)

        self.phase_table = PhaseTable(self)

    def update_options(self) -> None:
        """Updates the options of the pulse parameters."""
        for event in self.events:
            for pulse_parameter in event.parameters.values():
                pulse_parameter.update_option(self)

    def add_blank_event(self, event_name: str, duration: float) -> Event:
        """Adds a blank event to the pulse sequence.

        Args:
            event_name (str): The name of the event
            duration (float): The duration of the event with a unit suffix (n, u, m)

        Returns:
            Event: The created event
        """
        event = self.create_event(event_name, duration)
        return event

    def add_pulse_event(
        self,
        event_name: str,
        duration: float,
        amplitude: float,
        phase: float,
        shape: Function = RectFunction(),
    ) -> Event:
        """Adds a pulse event to the pulse sequence.

        Args:
            event_name (str): The name of the event
            duration (float): The duration of the event with a unit suffix (n, u, m)
            amplitude (float): The amplitude of the transmit pulse in percent (min 0, max 100)
            phase (float): The phase of the transmit pulse
            shape (Function): The shape of the transmit pulse

        Returns:
            Event: The created event
        """
        event = self.create_event(event_name, duration)
        self.set_tx_amplitude(event, amplitude)
        self.set_tx_phase(event, phase)
        self.set_tx_shape(event, shape)

        self.update_options()

        return event

    def add_readout_event(self, event_name: str, duration: float) -> Event:
        """Adds a readout event to the pulse sequence.

        Args:
            event_name (str): The name of the event
            duration (float): The duration of the event with a unit suffix (n, u, m)

        Returns:
            Event: The created event
        """
        event = self.create_event(event_name, duration)
        self.set_rx(event, True)

        return event

    # TX Specific functions

    def set_tx_amplitude(self, event: Event | str, amplitude: float) -> None:
        """Sets the relative amplitude of the transmit pulse in percent (larger 0 - max 100).

        Args:
            event (Event | str): The event to set the amplitude for or the name of the event
            amplitude (float): The amplitude of the transmit pulse in percent
        """
        if isinstance(event, str):
            event = self.get_event_by_name(event)

        if amplitude <= 0 or amplitude > 100:
            raise ValueError(
                "Amplitude needs to be larger than 0 and smaller or equal to 100"
            )

        event.parameters[self.TX_PULSE].get_option_by_name(
            TXPulse.RELATIVE_AMPLITUDE
        ).value = amplitude

    def set_tx_phase(self, event: Event | str, phase: float) -> None:
        """Sets the phase of the transmitter.

        Args:
            event (Event | str): The event to set the phase for or the name of the event
            phase (float): The phase of the transmitter
        """
        if isinstance(event, str):
            event = self.get_event_by_name(event)

        event.parameters[self.TX_PULSE].get_option_by_name(
            TXPulse.TX_PHASE
        ).value = phase

    def set_tx_shape(self, event: Event | str, shape: Function) -> None:
        """Sets the shape of the transmit pulse.

        Args:
            event (Event | str): The event to set the shape for or the name of the event
            shape (Function): The shape of the transmit pulse
        """
        if isinstance(event, str):
            event = self.get_event_by_name(event)

        event.parameters[self.TX_PULSE].get_option_by_name(
            TXPulse.TX_PULSE_SHAPE
        ).value = shape

    def set_tx_n_phase_cycles(self, event: Event | str, n_phase_cycles: int) -> None:
        """Sets the number of phase cycles for the transmit pulse.

        Args:
            event (Event | str): The event to set the number of phase cycles for or the name of the event
            n_phase_cycles (int): The number of phase cycles
        """
        if isinstance(event, str):
            event = self.get_event_by_name(event)

        event.parameters[self.TX_PULSE].get_option_by_name(
            TXPulse.N_PHASE_CYCLES
        ).value = n_phase_cycles

        self.update_options()

    def set_tx_phase_cycle_group(
        self, event: Event | str, phase_cycle_group: int
    ) -> None:
        """Sets the phase cycle group for the transmit pulse.

        Args:
            event (Event | str): The event to set the phase cycle group for or the name of the event
            phase_cycle_group (int): The phase cycle group
        """
        if isinstance(event, str):
            event = self.get_event_by_name(event)

        event.parameters[self.TX_PULSE].get_option_by_name(
            TXPulse.PHASE_CYCLE_GROUP
        ).value = phase_cycle_group

        self.update_options()

    # RX Specific functions

    def set_rx(self, event: Event | str, rx: bool) -> None:
        """Sets the receiver on or off.

        Args:
            event (Event | str): The event to set the receiver state for or the name of the event
            rx (bool): The receiver state
        """
        if isinstance(event, str):
            event = self.get_event_by_name(event)

        event.parameters[self.RX_READOUT].get_option_by_name(RXReadout.RX).value = rx

    def set_rx_phase(self, event: Event | str, phase: list) -> None:
        """Sets the phase of the receiver.

        Args:
            event (Event | str): The event to set the phase for or the name of the event
            phase (list): The phase of the receiver
        """
        if isinstance(event, str):
            event = self.get_event_by_name(event)

        rx_table = event.parameters[self.RX_READOUT].get_option_by_name(RXReadout.READOUT_SCHEME)

        # Check that the number of phases is the same as the number of phase cycles
        if len(phase) != self.get_n_phase_cycles():
            raise ValueError(
                f"Number of phases ({len(phase)}) needs to be the same as the number of phase cycles ({self.get_n_phase_cycles()})"
            )

        # Set the values
        rx_table.set_column(RXReadout.PHASE, phase)
        

    def get_n_phase_cycles(self) -> int:
        """Returns the number of phase cycles of the pulse sequence.

        Returns:
            int: The number of phase cycles
        """
        return self.phase_table.n_phase_cycles