"""Contains the PulseSequence class that is used to store a pulse sequence and its events."""

import logging
import importlib.metadata

logger = logging.getLogger(__name__)


class PulseSequence:
    """A pulse sequence is a collection of events that are executed in a certain order.

    Args:
        name (str): The name of the pulse sequence

    Attributes:
        name (str): The name of the pulse sequence
        events (list): The events of the pulse sequence
    """

    def __init__(self, name, version = None) -> None:
        """Initializes the pulse sequence."""
        self.name = name
        # Saving version to check for compatability of saved sequence
        if version is not None:
            self.version = version
        else:
            self.version = importlib.metadata.version("nqrduck_spectrometer")
        self.events = list()

    def get_event_names(self) -> list:
        """Returns a list of the names of the events in the pulse sequence.

        Returns:
            list: The names of the events
        """
        return [event.name for event in self.events]
    
    def add_event(self, event_name: str, duration: float) -> None:
        """Add a new event to the pulse sequence.

        Args:
            event_name (str): The name of the event
            duration (float): The duration of the event
        """
        self.events.append(self.Event(event_name, f"{float(duration):.16g}u"))
        

    def delete_event(self, event_name: str) -> None:
        """Deletes an event from the pulse sequence.

        Args:
            event_name (str): The name of the event to delete
        """
        for event in self.events:
            if event.name == event_name:
                self.events.remove(event)
                break

    def to_json(self):
        """Returns a dict with all the data in the pulse sequence.

        Returns:
            dict: The dict with the sequence data
        """
        # Get the versions of this package
        data = {"name": self.name, "version" : self.version, "events": []}
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
            obj = cls(sequence["name"], version = sequence["version"])
        except KeyError:
            logger.error("Pulse sequence version not found")
            raise KeyError("Pulse sequence version not found")
            
        for event_data in sequence["events"]:
            obj.events.append(cls.Event.load_event(event_data, pulse_parameter_options))

        return obj

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
