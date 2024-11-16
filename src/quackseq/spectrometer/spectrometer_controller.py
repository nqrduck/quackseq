"""Base class for all spectrometer controllers."""

import logging

from quackseq.pulseparameters import RXReadout
from quackseq.pulsesequence import QuackSequence

logger = logging.getLogger(__name__)


class SpectrometerController:
    """The base class for all spectrometer controllers."""

    def run_sequence(self, sequence):
        """Starts the measurement.

        This method should be called when the measurement is started.
        """
        raise NotImplementedError

    def set_frequency(self, value: float):
        """Sets the frequency of the spectrometer."""
        raise NotImplementedError

    def set_averages(self, value: int):
        """Sets the number of averages."""
        raise NotImplementedError

    def translate_rx_event(self, sequence: QuackSequence) -> tuple:
        """This method translates the RX event of the pulse sequence to the limr object.

        Returns:
        tuple: A tuple containing the start and stop time of the RX event in µs and the phase of the RX event and the phase as a list of different phase values for each phasecycle.
        """
        # This is a correction factor for the RX event. The offset of the first pulse is 2.2µs longer than from the specified samples.
        events = sequence.events

        previous_events_duration = 0
        # offset = 0
        rx_duration = 0
        for event in events:
            logger.debug("Event %s has parameters: %s", event.name, event.parameters)
            for parameter in event.parameters.values():
                logger.debug(
                    "Parameter %s has options: %s", parameter.name, parameter.options
                )

                if (
                    parameter.name == sequence.RX_READOUT
                    and parameter.get_option_by_name(RXReadout.RX).value
                ):
                    # Get the length of all previous events
                    previous_events = events[: events.index(event)]
                    previous_events_duration = sum(
                        [event.duration for event in previous_events]
                    )
                    rx_duration = event.duration

                    # We get the RX phase from the RX event
                    readout_scheme = parameter.get_option_by_name(
                        RXReadout.READOUT_SCHEME
                    )
                    readout_scheme = readout_scheme.get_value()[0]

        rx_begin = float(previous_events_duration)
        if rx_duration:
            rx_stop = rx_begin + float(rx_duration)
            return rx_begin * 1e6, rx_stop * 1e6, readout_scheme

        else:
            return None, None, None

    def calculate_simulation_length(self, sequence: QuackSequence) -> float:
        """This method calculates the simulation length based on the settings and the pulse sequence.

        Returns:
            float: The simulation length in seconds.
        """
        events = sequence.events
        simulation_length = 0
        for event in events:
            simulation_length += event.duration
        return simulation_length
