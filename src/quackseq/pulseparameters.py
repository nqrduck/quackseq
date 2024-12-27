"""Contains the classes for the pulse parameters of the spectrometer. It includes the functions and the options for the pulse parameters.

Todo:
    * This shouldn't be in the spectrometer module. It should be in it"s own pulse sequence module.
"""

from __future__ import annotations
import logging
from typing import override

import numpy as np
from numpy.core.multiarray import array as array

from quackseq.options import (
    TableOption,
    BooleanOption,
    FunctionOption,
    NumericOption,
    Option,
)
from quackseq.functions import (
    RectFunction,
    SincFunction,
    GaussianFunction,
    CustomFunction,
)

logger = logging.getLogger(__name__)


class PulseParameter:
    """A pulse parameter is a value that can be different for each event in a pulse sequence.

    E.g. the transmit pulse power or the phase of the transmit pulse.

    Args:
        name (str) : The name of the pulse parameter

    Attributes:
        name (str) : The name of the pulse parameter
        options (OrderedDict) : The options of the pulse parameter
    """

    def __init__(self, name: str):
        """Initializes the pulse parameter.

        Arguments:
            name (str) : The name of the pulse parameter
        """
        self.name = name
        self.options = list()

    def add_option(self, option: Option) -> None:
        """Adds an option to the pulse parameter.

        Args:
            option (Option) : The option to add
        """
        self.options.append(option)

    def get_options(self) -> list:
        """Gets the options of the pulse parameter.

        Returns:
            list : The options of the pulse parameter
        """
        return self.options

    def get_option_by_name(self, name: str) -> Option:
        """Gets an option by its name.

        Args:
            name (str) : The name of the option

        Returns:
            Option : The option with the specified name

        Raises:
            ValueError : If no option with the specified name is found
        """
        for option in self.options:
            if option.name == name:
                return option
        raise ValueError(f"Option with name {name} not found")

    def update_option(self, sequence: "QuackSequence") -> None:
        """Generic update option method for pulse parameters.

        This can be implemented by subclasses to update the options of the pulse parameter whenever the parameter is called (e.g. in the GUI).

        Args:
            sequence (QuackSequence): The sequence to update the options from.
        """
        pass


class TXPulse(PulseParameter):
    """Basic TX Pulse Parameter. It includes options for the relative amplitude, the phase and the pulse shape.

    Args:
        name (str): The name of the pulse parameter.
    """

    RELATIVE_AMPLITUDE = "Relative TX Amplitude (%)"
    TX_PHASE = "TX Phase"
    TX_PULSE_SHAPE = "TX Pulse Shape"
    N_PHASE_CYCLES = "Number of Phase Cycles"
    PHASE_CYCLE_GROUP = "Phase Cycle Group"

    def __init__(self, name: str) -> None:
        """Initializes the TX Pulse Parameter.

        It adds the options for the relative amplitude, the phase and the pulse shape.
        """
        super().__init__(name)
        self.add_option(
            NumericOption(
                self.RELATIVE_AMPLITUDE,
                0,
                is_float=False,
                min_value=0,
                max_value=100,
                slider=True,
            )
        )
        self.add_option(NumericOption(self.TX_PHASE, 0))
        self.add_option(
            NumericOption(
                self.N_PHASE_CYCLES,
                1,
                is_float=False,
                min_value=1,
                max_value=360,
                slider=False,
            )
        )
        self.add_option(
            NumericOption(
                self.PHASE_CYCLE_GROUP,
                0,
                is_float=False,
                min_value=0,
                max_value=10,
                slider=False,
            )
        )
        self.add_option(
            FunctionOption(
                self.TX_PULSE_SHAPE,
                [
                    RectFunction(),
                    SincFunction(),
                    GaussianFunction(),
                    CustomFunction(),
                ],
            ),
        )

    def get_phases(self):
        """Gets the phase of the TX Pulse.

        Returns:
            np.array : The phases of the TX Pulse
        """
        n_phase_cycles = self.get_option_by_name(self.N_PHASE_CYCLES).value

        phase = self.get_option_by_name(self.TX_PHASE).value

        return (np.linspace(0, 360, int(n_phase_cycles), endpoint=False) + phase) % 360


class RXReadout(PulseParameter):
    """Basic PulseParameter for the RX Readout. It includes an option for the RX Readout state.

    Args:
        name (str): The name of the pulse parameter.

    Attributes:
        RX (str): The RX Readout state.
    """

    RX = "Enable RX Readout"
    READOUT_SCHEME = "Readout Scheme"
    PHASE = "Phase"

    def __init__(self, name) -> None:
        """Initializes the RX Readout PulseParameter.

        It adds an option for the RX Readout state.
        """
        super().__init__(name)
        self.add_option(BooleanOption(self.RX, False))

        # Readout Scheme:
        readout_option = TableOption(self.READOUT_SCHEME)

        # Add Phase Option to Readout Scheme
        phase_option = NumericOption

        readout_option.add_column(self.PHASE, phase_option, 0)

        # Set number of rows to default value
        readout_option.set_n_rows(1)

        self.add_option(readout_option)

    @override
    def update_option(self, sequence: "QuackSequence") -> None:
        """Adjusts the number of rows in the table option based on the number of phase cycles in the sequence."""
        n_phase_cycles = sequence.get_n_phase_cycles()
        readout_option = self.get_option_by_name(self.READOUT_SCHEME)
        readout_option.set_n_rows(n_phase_cycles)
        logger.debug(f"Updated RX Readout option with {n_phase_cycles} rows")

    def set_phase(self, phase: list) -> None:
        """Sets the phase of the RX Readout.

        Args:
            phase (list): The phase of the RX Readout
        """
        readout_option = self.get_option_by_name(self.READOUT_SCHEME)
        readout_option.set_column(self.PHASE, phase)


class Gate(PulseParameter):
    """Basic PulseParameter for the Gate. It includes an option for the Gate state.

    Args:
        name (str): The name of the pulse parameter.

    Attributes:
        GATE_STATE (str): The Gate state.
    """

    GATE_STATE = "Gate State"

    def __init__(self, name) -> None:
        """Initializes the Gate PulseParameter.

        It adds an option for the Gate state.
        """
        super().__init__(name)
        self.add_option(BooleanOption(self.GATE_STATE, False))
