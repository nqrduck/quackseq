"""The phase table module contains the PhaseTable class, which interprets the TX parameters of a QuackSequence object and then generates a table of different phase values and signs for each phasecycle."""

import logging
import numpy as np
from collections import OrderedDict

from quackseq.pulseparameters import TXPulse

logger = logging.getLogger(__name__)


class PhaseTable:
    """A phase table interprets the TX parameters of a QuackSequence object and then generates a table of different phase values and signs for each phasecycle."""

    def __init__(self, quackseq):
        """Initializes the phase table."""
        self.quackseq = quackseq
        # Set phase array to default value
        self.phase_array = np.array([])
        self.generate_phase_array()

    def generate_phase_array(self):
        """Generate a list of phases for each phasecycle in the sequence.

        Returns:
            phase_array (np.array): A table of phase values for each phasecycle.
                                    The columns are the values for the different TX pulse parameters and the rows are the different phase cycles.
        """
        phase_table = OrderedDict()
        events = self.quackseq.events

        # If there are no events, return an empty array
        if not events:
            return np.array([])

        for event in events:
            for parameter in event.parameters.values():
                if parameter.name == self.quackseq.TX_PULSE:
                    if (
                        parameter.get_option_by_name(TXPulse.RELATIVE_AMPLITUDE).value
                        > 0
                    ):
                        phase_group = parameter.get_option_by_name(
                            TXPulse.PHASE_CYCLE_GROUP
                        ).value

                        phase_values = parameter.get_phases()

                        phase_table[parameter] = (phase_group, phase_values)

        logger.info(phase_table)

        # If no TX events are found, return an empty array
        if not phase_table:
            return np.array([])

        # First we make sure that all phase groups are in direct sucessive order. E.if there is a a phase group 0 and phase group 2 then phase group 2 will be renamed to 1.
        phase_groups = [phase_group for phase_group, _ in phase_table.values()]
        phase_groups = list(set(phase_groups))
        phase_groups.sort()
        for i, phase_group in enumerate(phase_groups):
            if i != phase_group:
                for parameter, (group, phase_values) in phase_table.items():
                    if group == phase_group:
                        phase_table[parameter] = (i, phase_values)

        logger.info(phase_table)

        # Now get the maximum phase group
        max_phase_group = int(
            max([phase_group for phase_group, _ in phase_table.values()])
        )

        logger.info(f"Max phase group: {max_phase_group}")

        # The columns of the phase table are the number of parameters in the phase table
        n_columns = len(phase_table)

        logger.info(f"Number of columns: {n_columns}")

        # The number of rows is the maximum number of phase values in a phase group multiplied for every phase group
        n_rows = 1
        max_phase_values = 1
        for i in range(max_phase_group + 1):
            for parameter, (group, phase_values) in phase_table.items():
                if max_phase_values < len(phase_values):
                    max_phase_values = len(phase_values)

            n_rows *= max_phase_values
            max_phase_values = 1

        # This should be four
        logger.info(f"Number of rows: {n_rows}")

        # Create the phase table
        phase_array = np.zeros((n_rows, n_columns))

        groups = [group for group, _ in phase_table.values()]
        groups = list(set(groups))

        group_phases = {}
        pulse_phases = {}

        for group in groups:
            # All the parameters that belong to the same group
            parameters = {
                parameter: phase_values
                for parameter, (p_group, phase_values) in phase_table.items()
                if p_group == group
            }

            # The maximum number of phase values in the group
            max_phase_values = max(
                [len(phase_values) for phase_values in parameters.values()]
            )

            # Fill up the phase tables of parameters that have less than the maximum number of phase values by repeating the values
            for parameter, phase_values in parameters.items():
                if len(phase_values) < max_phase_values:
                    phase_values = np.tile(
                        phase_values, int(np.ceil(max_phase_values / len(phase_values)))
                    )
                    pulse_phases[parameter] = phase_values
                    parameters[parameter] = phase_values
                else:
                    pulse_phases[parameter] = phase_values

            logger.info(f"Parameters for group {group}: {parameters}")
            group_phases[group] = parameters

        def get_group_phases(group):
            current_group_phases = []

            phase_length = len(list(group_phases[group].values())[0])
            group_parameters = list(group_phases[group].items())
            first_parameter = group_parameters[0][0]
            logger.debug(f"First parameter: {first_parameter}")

            for i in range(phase_length):
                for parameter, phases in group_phases[group].items():
                    if parameter == first_parameter:
                        current_group_phases.append([parameter, phases[i]])

            sub_group_phases = []

            if group + 1 in group_phases:
                sub_group_phases = get_group_phases(group + 1)

            total_group_phases = []

            for parameter, phase in current_group_phases:
                for sub_group_phase in sub_group_phases:
                    total_group_phases.append([parameter, phase, *sub_group_phase])

            if not total_group_phases:
                total_group_phases = current_group_phases

            for i in range(phase_length):
                for parameter, phases in group_phases[group].items():
                    if parameter != first_parameter:
                        try:
                            total_group_phases[i] += [parameter, phases[i]]
                        except IndexError:
                            logger.info(
                                f"Index Error 1: Parameter {parameter}, Phases: {phases}"
                            )

            return total_group_phases

        all_phases = get_group_phases(0)

        for row, phases in enumerate(all_phases):
            phases = [phases[i : i + 2] for i in range(0, len(phases), 2)]

            for phase in phases:
                parameter, phase_value = phase
                column = list(phase_table.keys()).index(parameter)
                try:
                    phase_array[row, column] = phase_value
                except IndexError as e:
                    logger.info(
                        f"Index error 2: {row}, {column}, {phase_value}, {phase}, {e}"
                    )

        logger.info(phase_array)

        # First set the phase array
        self.phase_array = phase_array

    @property
    def phase_array(self) -> np.array:
        """The phase array of the sequence."""
        return self._phase_array

    @phase_array.setter
    def phase_array(self, phase_array: np.array):
        self._phase_array = phase_array

    @property
    def n_phase_cycles(self) -> int:
        """The number of phase cycles in the sequence."""
        # Calculate the number of phase cycles
        self.generate_phase_array()
        return self.phase_array.shape[0]

    @property
    def n_parameters(self) -> int:
        """The number of TX pulse parameters in the sequence."""
        return self.phase_array.shape[1]