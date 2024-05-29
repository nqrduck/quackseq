"""The controller module for the simulator spectrometer."""

import logging
from datetime import datetime
import numpy as np

from quackseq.spectrometer.spectrometer_controller import SpectrometerController
from quackseq.measurement import Measurement
from quackseq.pulseparameters import TXPulse, RXReadout
from quackseq.pulsesequence import QuackSequence

from nqr_blochsimulator.classes.pulse import PulseArray
from nqr_blochsimulator.classes.sample import Sample
from nqr_blochsimulator.classes.simulation import Simulation

logger = logging.getLogger(__name__)


class SimulatorController(SpectrometerController):
    """The controller class for the nqrduck simulator module."""

    def __init__(self, model):
        """Initializes the SimulatorController."""
        super().__init__()
        self.model = model

    def run_sequence(self, sequence: QuackSequence) -> None:
        """This method  is called when the start_measurement signal is received from the core.

        It will becalled if the simulator is the  active  spectrometer.
        This will start the simulation based on the settings and the pulse sequence.
        """
        logger.debug("Starting simulation")
        sample = self.get_sample_from_settings()
        logger.debug("Sample: %s", sample.name)

        dwell_time = self.calculate_dwelltime(sequence)
        logger.debug("Dwell time: %s", dwell_time)

        try:
            pulse_array = self.translate_pulse_sequence(sequence, dwell_time)
        except AttributeError:
            logger.warning("Could not translate pulse sequence")
            return

        simulation = self.get_simulation(sample, pulse_array)

        result = simulation.simulate()

        tdx = (
            np.linspace(0, float(self.calculate_simulation_length(sequence)), len(result)) * 1e6
        )

        rx_begin, rx_stop = self.translate_rx_event(sequence)
        # If we have a RX event, we need to cut the result to the RX event
        if rx_begin and rx_stop:
            evidx = np.where((tdx > rx_begin) & (tdx < rx_stop))[0]
            tdx = tdx[evidx]
            result = result[evidx]

        # Measurement name date + module + target frequency + averages + sequence name
        name = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Simulator - {self.model.target_frequency / 1e6} MHz - {self.model.averages} averages - {sequence.name}"
        logger.debug(f"Measurement name: {name}")

        measurement_data = Measurement(
            name,
            tdx,
            result / simulation.averages,
            sample.resonant_frequency,
            # frequency_shift=self.module.model.if_frequency,
        )

        return measurement_data

    def get_sample_from_settings(self) -> Sample:
        """This method creates a sample object based on the settings in the model.

        Returns:
            Sample: The sample object created from the settings.
        """
        model = self.model
        atom_density = None
        sample_volume = None
        sample_length = None
        sample_diameter = None

        for samplesetting in model.settings[self.model.SAMPLE]:
            logger.debug("Sample setting: %s", samplesetting.name)

            if samplesetting.name == model.NAME:
                name = samplesetting.value
            elif samplesetting.name == model.DENSITY:
                density = float(samplesetting.value)
            elif samplesetting.name == model.MOLAR_MASS:
                molar_mass = float(samplesetting.value)
            elif samplesetting.name == model.RESONANT_FREQUENCY:
                resonant_frequency = float(samplesetting.value)
            elif samplesetting.name == model.GAMMA:
                gamma = float(samplesetting.value)
            elif samplesetting.name == model.NUCLEAR_SPIN:
                nuclear_spin = float(samplesetting.value)
            elif samplesetting.name == model.SPIN_FACTOR:
                spin_factor = float(samplesetting.value)
            elif samplesetting.name == model.POWDER_FACTOR:
                powder_factor = float(samplesetting.value)
            elif samplesetting.name == model.FILLING_FACTOR:
                filling_factor = float(samplesetting.value)
            elif samplesetting.name == model.T1:
                T1 = float(samplesetting.value)
            elif samplesetting.name == model.T2:
                T2 = float(samplesetting.value)
            elif samplesetting.name == model.T2_STAR:
                T2_star = float(samplesetting.value)
            elif samplesetting.name == model.ATOM_DENSITY:
                atom_density = float(samplesetting.value)
            elif samplesetting.name == model.SAMPLE_VOLUME:
                sample_volume = float(samplesetting.value)
            elif samplesetting.name == model.SAMPLE_LENGTH:
                sample_length = float(samplesetting.value)
            elif samplesetting.name == model.SAMPLE_DIAMETER:
                sample_diameter = float(samplesetting.value)
            else:
                logger.warning("Unknown sample setting: %s", samplesetting.name)
                self.module.nqrduck_signal.emit(
                    "notification",
                    ["Error", "Unknown sample setting: " + samplesetting.name],
                )
                return None

        sample = Sample(
            name=name,
            density=density,
            molar_mass=molar_mass,
            resonant_frequency=resonant_frequency,
            gamma=gamma,
            nuclear_spin=nuclear_spin,
            spin_factor=spin_factor,
            powder_factor=powder_factor,
            filling_factor=filling_factor,
            T1=T1,
            T2=T2,
            T2_star=T2_star,
            atom_density=atom_density,
            sample_volume=sample_volume,
            sample_length=sample_length,
            sample_diameter=sample_diameter,
        )
        return sample

    def translate_pulse_sequence(self,  sequence : QuackSequence, dwell_time: float) -> PulseArray:
        """This method translates the pulse sequence from the core to a PulseArray object needed for the simulation.

        Args:
            sequence (QuackSequence): The pulse sequence from the core.
            dwell_time (float): The dwell time in seconds.

        Returns:
            PulseArray: The pulse sequence translated to a PulseArray object.
        """
        events = sequence.events

        amplitude_array = list()
        for event in events:
            logger.debug("Event %s has parameters: %s", event.name, event.parameters)
            for parameter in event.parameters.values():
                logger.debug(
                    "Parameter %s has options: %s", parameter.name, parameter.options
                )

                if (
                    parameter.name == sequence.TX_PULSE
                    and parameter.get_option_by_name(TXPulse.RELATIVE_AMPLITUDE).value
                    > 0
                ):
                    logger.debug(f"Adding pulse: {event.duration} s")
                    # If we have a pulse, we need to add it to the pulse array
                    pulse_shape = parameter.get_option_by_name(
                        TXPulse.TX_PULSE_SHAPE
                    ).value
                    pulse_amplitude = abs(
                        pulse_shape.get_pulse_amplitude(
                            event.duration, resolution=dwell_time
                        )
                    )

                    amplitude_array.append(pulse_amplitude)
                elif (
                    parameter.name == sequence.TX_PULSE
                    and parameter.get_option_by_name(TXPulse.RELATIVE_AMPLITUDE).value
                    == 0
                ):
                    # If we have a wait, we need to add it to the pulse array
                    amplitude_array.append(np.zeros(int(event.duration / dwell_time)))

        amplitude_array = np.concatenate(amplitude_array)

        # This has not yet been implemented right now the phase is always 0
        phase_array = np.zeros(len(amplitude_array))

        pulse_array = PulseArray(
            pulseamplitude=amplitude_array,
            pulsephase=phase_array,
            dwell_time=float(dwell_time),
        )

        return pulse_array

    def get_simulation(self, sample: Sample, pulse_array: PulseArray) -> Simulation:
        """This method creates a simulation object based on the settings and the pulse sequence.

        Args:
            sample (Sample): The sample object created from the settings.
            pulse_array (PulseArray): The pulse sequence translated to a PulseArray object.

        Returns:
            Simulation: The simulation object created from the settings and the pulse sequence.
        """
        model = self.model

        # noise = float(model.get_setting_by_name(model.NOISE).value)
        simulation = Simulation(
            sample=sample,
            pulse=pulse_array,
            number_isochromats=int(
                model.get_setting_by_name(model.NUMBER_ISOCHROMATS).value
            ),
            initial_magnetization=float(
                model.get_setting_by_name(model.INITIAL_MAGNETIZATION).value
            ),
            gradient=float(model.get_setting_by_name(model.GRADIENT).value),
            noise=float(model.get_setting_by_name(model.NOISE).value),
            length_coil=float(model.get_setting_by_name(model.LENGTH_COIL).value),
            diameter_coil=float(model.get_setting_by_name(model.DIAMETER_COIL).value),
            number_turns=float(model.get_setting_by_name(model.NUMBER_TURNS).value),
            q_factor_transmit=float(
                model.get_setting_by_name(model.Q_FACTOR_TRANSMIT).value
            ),
            q_factor_receive=float(
                model.get_setting_by_name(model.Q_FACTOR_RECEIVE).value
            ),
            power_amplifier_power=float(
                model.get_setting_by_name(model.POWER_AMPLIFIER_POWER).value
            ),
            gain=float(model.get_setting_by_name(model.GAIN).value),
            temperature=float(model.get_setting_by_name(model.TEMPERATURE).value),
            averages=int(model.averages),
            loss_TX=float(model.get_setting_by_name(model.LOSS_TX).value),
            loss_RX=float(model.get_setting_by_name(model.LOSS_RX).value),
            conversion_factor=float(
                model.get_setting_by_name(model.CONVERSION_FACTOR).value
            ),
        )
        return simulation

    def calculate_dwelltime(self, sequence : QuackSequence) -> float:
        """This method calculates the dwell time based on the settings and the pulse sequence.

        Returns:
            float: The dwell time in seconds.
        """
        n_points = int(
            self.model.get_setting_by_name(self.model.NUMBER_POINTS).value
        )
        simulation_length = self.calculate_simulation_length(sequence)
        dwell_time = simulation_length / n_points
        return dwell_time

    def calculate_simulation_length(self, sequence : QuackSequence) -> float:
        """This method calculates the simulation length based on the settings and the pulse sequence.

        Returns:
            float: The simulation length in seconds.
        """
        events = sequence.events
        simulation_length = 0
        for event in events:
            simulation_length += event.duration
        return simulation_length

    def translate_rx_event(self, sequence : QuackSequence) -> tuple:
        """This method translates the RX event of the pulse sequence to the limr object.

        Returns:
        tuple: A tuple containing the start and stop time of the RX event in µs
        """
        # This is a correction factor for the RX event. The offset of the first pulse is 2.2µs longer than from the specified samples.
        events =  sequence.events

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

        rx_begin = float(previous_events_duration)
        if rx_duration:
            rx_stop = rx_begin + float(rx_duration)
            return rx_begin * 1e6, rx_stop * 1e6

        else:
            return None, None

    def set_frequency(self, value: str) -> None:
        """This method is called when the set_frequency signal is received from the core.

        For the simulator this just prints a  warning that the simulator is selected.

        Args:
            value (str) : The new frequency in MHz.
        """
        logger.debug("Setting frequency to: %s", value)
        try:
            self.module.model.target_frequency = float(value)
            logger.debug("Successfully set frequency to: %s", value)
        except ValueError:
            logger.warning("Could not set frequency to: %s", value)
            self.module.nqrduck_signal.emit(
                "notification", ["Error", "Could not set frequency to: " + value]
            )
            self.module.nqrduck_signal.emit("failure_set_frequency", value)

    def set_averages(self, value: str) -> None:
        """This method is called when the set_averages signal is received from the core.

        It sets the averages in the model used for the simulation.

        Args:
            value (str): The value to set the averages to.
        """
        logger.debug("Setting averages to: %s", value)
        try:
            self.module.model.averages = int(value)
            logger.debug("Successfully set averages to: %s", value)
        except ValueError:
            logger.warning("Could not set averages to: %s", value)
            self.module.nqrduck_signal.emit(
                "notification", ["Error", "Could not set averages to: " + value]
            )
            self.module.nqrduck_signal.emit("failure_set_averages", value)
