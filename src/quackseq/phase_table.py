import logging
import numpy as np
from collections import OrderedDict

from quackseq.pulsesequence import QuackSequence
from quackseq.pulseparameters import TXPulse

logger = logging.getLogger(__name__)


class PhaseTable:
    """A phase table interprets the TX parameters of a QuackSequence object and then generates a table of different phase values and signs for each phasecycle."""

    def __init__(self, quackseq):
        self.quackseq = quackseq
        self.phase_table = self.generate_phase_table()

    def generate_phase_table(self):
        """Generate a list of phases for each phasecycle in the sequence."""

        phase_table = OrderedDict()
        events = self.quackseq.events

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
        max_phase_group = max([phase_group for phase_group, _ in phase_table.values()])

        logger.info(f"Max phase group: {max_phase_group}")

        # The columns of the phase table are the number of parameters in the phase table
        n_columns = len(phase_table)

        logger.info(f"Number of columns: {n_columns}")

        # The number of rows is the maximum number of phase values in a phase group multiplied for every phase group
        n_rows = 1
        for i in range(max_phase_group + 1):
            for parameter, (group, phase_values) in phase_table.items():
                if group == i:
                    n_rows *= len(phase_values)
                    break

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
                        phase_values, max_phase_values // len(phase_values)
                    )
                    pulse_phases[parameter] = phase_values
                    logger.info(
                        f"Phase values for parameter {parameter}: {phase_values}"
                    )
                    parameters[parameter] = phase_values
                else:
                    pulse_phases[parameter] = phase_values
                    logger.info(
                        f"Phase values for parameter {parameter}: {phase_values}"
                    )

            logger.info(f"Parameters for group {group}: {parameters}")
            group_phases[group] = parameters

        def get_group_phases(group):
            current_group_phases = []

            phase_length = len(list(group_phases[group].values())[0])
            group_parameters = list(group_phases[group].items())
            first_parameter = group_parameters[0][0]

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
                        total_group_phases[i] += [parameter, phases[i]]

            return total_group_phases

        all_phases = get_group_phases(0)

        for row, phases in enumerate(all_phases):
            phases = [phases[i : i + 2] for i in range(0, len(phases), 2)]
            logger.info(f"Phases: {phases}")

            for phase in phases:
                parameter, phase_value = phase
                column = list(phase_table.keys()).index(parameter)
                phase_array[row, column] = phase_value

        # logger.info(f"Phase table: {phase_table}")
        # logger.info(f"Pulse phases: {pulse_phases}")

        # for column in range(n_columns):

        # Get the parameter
        #    parameter = list(phase_table.keys())[column]

        # The division factor is the number of rows divided by the length of the pulse phases of the parameter
        #    logger.info(f"Len of pulse phases: {(pulse_phases[parameter])}")
        #    division_factor = (n_rows // len(pulse_phases[parameter]))

        #    logger.info(f"Division factor: {division_factor}")

        #    for row in range(n_rows):
        # The phase value is the row index divided by the division factor
        #        phase_array[row, column] = pulse_phases[parameter][row // division_factor]

        logger.info(phase_array)

        return phase_table
