import logging
from collections import OrderedDict

from quackseq.pulseparameters import Option
from quackseq.helpers import UnitConverter

logger = logging.getLogger(__name__)


class Event:
    """An event is a part of a pulse sequence. It has a name and a duration and different parameters that have to be set.

    Args:
        name (str): The name of the event
        duration (str): The duration of the event

    Attributes:
        name (str): The name of the event
        duration (str): The duration of the event
        parameters (OrderedDict): The parameters of the event
    """

    def __init__(self, name: str, duration: str) -> None:
        """Initializes the event."""
        self.parameters = OrderedDict()
        self.name = name
        self.duration = duration

    def add_parameter(self, parameter) -> None:
        """Adds a parameter to the event.

        Args:
            parameter: The parameter to add
        """
        self.parameters.append(parameter)

    def on_duration_changed(self, duration: str) -> None:
        """This method is called when the duration of the event is changed.

        Args:
            duration (str): The new duration of the event
        """
        logger.debug("Duration of event %s changed to %s", self.name, duration)
        self.duration = duration

    @classmethod
    def load_event(cls, event, pulse_parameter_options):
        """Loads an event from a dict.

        The pulse paramter options are needed to load the parameters
        and determine if the correct spectrometer is active.

        Args:
            event (dict): The dict with the event data
            pulse_parameter_options (dict): The dict with the pulse parameter options

        Returns:
            Event: The loaded event
        """
        obj = cls(event["name"], event["duration"])
        for parameter in event["parameters"]:
            for pulse_parameter_option in pulse_parameter_options.keys():
                # This checks if the pulse paramter options are the same as the ones in the pulse sequence
                if pulse_parameter_option == parameter["name"]:
                    pulse_parameter_class = pulse_parameter_options[
                        pulse_parameter_option
                    ]
                    obj.parameters[pulse_parameter_option] = pulse_parameter_class(
                        parameter["name"]
                    )
                    # Delete the default instances of the pulse parameter options
                    obj.parameters[pulse_parameter_option].options = []
                    for option in parameter["value"]:
                        obj.parameters[pulse_parameter_option].options.append(
                            Option.from_json(option)
                        )

        return obj

    @property
    def duration(self):
        """The duration of the event."""
        return self._duration

    @duration.setter
    def duration(self, duration: str):
        # Duration needs to be a positive number
        try:
            duration = UnitConverter.to_float(duration)
        except ValueError:
            raise ValueError("Duration needs to be a number")
        if duration < 0:
            raise ValueError("Duration needs to be a positive number")

        self._duration = duration
