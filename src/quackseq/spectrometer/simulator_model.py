"""The model module for the simulator spectrometer."""

import logging
from quackseq.spectrometer.spectrometer_model import SpectrometerModel
from quackseq.spectrometer.spectrometer_settings import IntSetting, FloatSetting, StringSetting
from quackseq.pulseparameters import TXPulse, RXReadout

logger = logging.getLogger(__name__)


class SimulatorModel(SpectrometerModel):
    """Model class for the simulator spectrometer."""

    # Simulation settings
    NUMBER_POINTS = "N. simulation points"
    NUMBER_ISOCHROMATS = "N. of isochromats"
    INITIAL_MAGNETIZATION = "Initial magnetization"
    GRADIENT = "Gradient (mT/m))"
    NOISE = "Noise (uV)"

    # Hardware settings
    LENGTH_COIL = "Length coil (m)"
    DIAMETER_COIL = "Diameter coil (m)"
    NUMBER_TURNS = "Number turns"
    Q_FACTOR_TRANSMIT = "Q factor Transmit"
    Q_FACTOR_RECEIVE = "Q factor Receive"
    POWER_AMPLIFIER_POWER = "PA power (W)"
    GAIN = "Gain"
    TEMPERATURE = "Temperature (K)"
    AVERAGES = "Averages"
    LOSS_TX = "Loss TX (dB)"
    LOSS_RX = "Loss RX (dB)"
    CONVERSION_FACTOR = "Conversion factor"

    # Sample settings, this will  be done in a separate module later on
    NAME = "Name"
    DENSITY = "Density (g/cm^3)"
    MOLAR_MASS = "Molar mass (g/mol)"
    RESONANT_FREQUENCY = "Resonant freq. (Hz)"
    GAMMA = "Gamma (Hz/T)"
    NUCLEAR_SPIN = "Nuclear spin"
    SPIN_FACTOR = "Spin factor"
    POWDER_FACTOR = "Powder factor"
    FILLING_FACTOR = "Filling factor"
    T1 = "T1 (s)"
    T2 = "T2 (s)"
    T2_STAR = "T2* (s)"
    ATOM_DENSITY = "Atom density (1/cm^3)"
    SAMPLE_VOLUME = "Sample volume (m^3)"
    SAMPLE_LENGTH = "Sample length (m)"
    SAMPLE_DIAMETER = "Sample diameter (m)"

    # Categories of the settings
    SIMULATION = "Simulation"
    HARDWARE = "Hardware"
    EXPERIMENTAL_Setup = "Experimental Setup"
    SAMPLE = "Sample"

    def __init__(self):
        """Initializes the SimulatorModel."""
        super().__init__()

        # Simulation settings
        number_of_points_setting = IntSetting(
            self.NUMBER_POINTS,
            8192,
            "Number of points used for the simulation. This influences the dwell time in combination with the total event simulation given by the pulse sequence.",
            min_value=0,
        )
        self.add_setting(
            number_of_points_setting,
            self.SIMULATION,
        )

        number_of_isochromats_setting = IntSetting(
            self.NUMBER_ISOCHROMATS,
            1000,
            "Number of isochromats used for the simulation. This influences the computation time.",
            min_value=0,
            max_value=10000,
        )
        self.add_setting(number_of_isochromats_setting, self.SIMULATION)

        initial_magnetization_setting = FloatSetting(
            self.INITIAL_MAGNETIZATION,
            1,
            "Initial magnetization",
            min_value=0,
        )
        self.add_setting(initial_magnetization_setting, self.SIMULATION)

        # This doesn't really do anything yet
        gradient_setting = FloatSetting(
            self.GRADIENT,
            1,
            "Gradient",
        )
        self.add_setting(gradient_setting, self.SIMULATION)

        noise_setting = FloatSetting(
            self.NOISE,
            2,
            "Adds a specified level of random noise to the simulation to mimic real-world signal variations.",
            min_value=0,
            max_value=100,
        )
        self.add_setting(noise_setting, self.SIMULATION)

        # Hardware settings
        coil_length_setting = FloatSetting(
            self.LENGTH_COIL,
            30e-3,
            "The length of the sample coil within the hardware setup.",
            min_value=1e-3,
        )
        self.add_setting(coil_length_setting, self.HARDWARE)

        coil_diameter_setting = FloatSetting(
            self.DIAMETER_COIL,
            8e-3,
            "The diameter of the sample coil.",
            min_value=1e-3,
        )
        self.add_setting(coil_diameter_setting, self.HARDWARE)

        number_turns_setting = FloatSetting(
            self.NUMBER_TURNS,
            8,
            "The total number of turns of the sample coil.",
            min_value=1,
        )
        self.add_setting(number_turns_setting, self.HARDWARE)

        q_factor_transmit_setting = FloatSetting(
            self.Q_FACTOR_TRANSMIT,
            80,
            "The quality factor of the transmit path, which has an effect on the field strength for excitation.",
            min_value=1,
        )
        self.add_setting(q_factor_transmit_setting, self.HARDWARE)

        q_factor_receive_setting = FloatSetting(
            self.Q_FACTOR_RECEIVE,
            80,
            "The quality factor of the receive path, which has an effect on the final SNR.",
            min_value=1,
        )
        self.add_setting(q_factor_receive_setting, self.HARDWARE)

        power_amplifier_power_setting = FloatSetting(
            self.POWER_AMPLIFIER_POWER,
            110,
            "The power output capability of the power amplifier, determines the strength of pulses that can be generated.",
            min_value=0.1,
        )
        self.add_setting(power_amplifier_power_setting, self.HARDWARE)

        gain_setting = FloatSetting(
            self.GAIN,
            6000,
            "The amplification factor of the receiver chain, impacting the final measured signal amplitude.",
            min_value=0.1,
        )
        self.add_setting(gain_setting, self.HARDWARE)

        temperature_setting = FloatSetting(
            self.TEMPERATURE,
            300,
            "The absolute temperature during the experiment. This influences the SNR of the measurement.",
            min_value=0.1,
            max_value=400,
        )
        self.add_setting(temperature_setting, self.EXPERIMENTAL_Setup)

        loss_tx_setting = FloatSetting(
            self.LOSS_TX,
            25,
            "The signal loss occurring in the transmission path, affecting the effective RF pulse power.",
            min_value=0.1,
            max_value=60,
        )
        self.add_setting(loss_tx_setting, self.EXPERIMENTAL_Setup)

        loss_rx_setting = FloatSetting(
            self.LOSS_RX,
            25,
            "The signal loss in the reception path, which can reduce the signal that is ultimately detected.",
            min_value=0.1,
            max_value=60,
        )
        self.add_setting(loss_rx_setting, self.EXPERIMENTAL_Setup)

        conversion_factor_setting = FloatSetting(
            self.CONVERSION_FACTOR,
            2884,
            "Conversion factor  (spectrometer units / V)",
        )
        self.add_setting(
            conversion_factor_setting,
            self.EXPERIMENTAL_Setup,
        )  # Conversion factor for the LimeSDR based spectrometer

        # Sample settings
        sample_name_setting = StringSetting(
            self.NAME,
            "BiPh3",
            "The name of the sample.",
        )
        self.add_setting(sample_name_setting, self.SAMPLE)

        density_setting = FloatSetting(
            self.DENSITY,
            1.585e6,
            "The density of the sample. This is used to calculate the number of spins in the sample volume.",
            min_value=0.1,
        )
        self.add_setting(density_setting, self.SAMPLE)

        molar_mass_setting = FloatSetting(
            self.MOLAR_MASS,
            440.3,
            "The molar mass of the sample. This is used to calculate the number of spins in the sample volume.",
            min_value=0.1,
        )
        self.add_setting(molar_mass_setting, self.SAMPLE)

        resonant_frequency_setting = FloatSetting(
            self.RESONANT_FREQUENCY,
            83.56e6,
            "The resonant frequency of the observed transition.",
            min_value=1e5,
        )
        self.add_setting(resonant_frequency_setting, self.SAMPLE)

        gamma_setting = FloatSetting(
            self.GAMMA,
            4.342e7,
            "The gyromagnetic ratio of the sample’s nuclei.",
            min_value=0,
        )
        self.add_setting(gamma_setting, self.SAMPLE)

        # This could be updated to a selection setting
        nuclear_spin_setting = FloatSetting(
            self.NUCLEAR_SPIN,
            9 / 2,
            "The nuclear spin of the sample’s nuclei.",
            min_value=0,
        )
        self.add_setting(nuclear_spin_setting, self.SAMPLE)

        spin_factor_setting = FloatSetting(
            self.SPIN_FACTOR,
            2,
            "The spin factor represents the scaling coefficient for observable nuclear spin transitions along the x-axis, derived from the Pauli I x 0 -matrix elements.",
            min_value=0,
        )
        self.add_setting(spin_factor_setting, self.SAMPLE)

        powder_factor_setting = FloatSetting(
            self.POWDER_FACTOR,
            0.75,
            "A factor representing the crystallinity of the solid sample. A value of 0.75 corresponds to a powder sample.",
            min_value=0,
            max_value=1,
        )
        self.add_setting(powder_factor_setting, self.SAMPLE)

        filling_factor_setting = FloatSetting(
            self.FILLING_FACTOR,
            0.7,
            "The ratio of the sample volume that occupies the coil’s sensitive volume.",
            min_value=0,
            max_value=1,
        )
        self.add_setting(filling_factor_setting, self.SAMPLE)

        t1_setting = FloatSetting(
            self.T1,
            83.5e-5,
            "The longitudinal or spin-lattice relaxation time of the sample, influencing signal recovery between pulses.",
            min_value=1e-6,
        )
        self.add_setting(t1_setting, self.SAMPLE)

        t2_setting = FloatSetting(
            self.T2,
            396e-6,
            "The transverse or spin-spin relaxation time, determining the rate at which spins dephase and the signal decays in the xy plane",
            min_value=1e-6,
        )
        self.add_setting(t2_setting, self.SAMPLE)

        t2_star_setting = FloatSetting(
            self.T2_STAR,
            50e-6,
            "The effective transverse relaxation time, incorporating effects of EFG inhomogeneities and other dephasing factors.",
            min_value=1e-6,
        )
        self.add_setting(t2_star_setting, self.SAMPLE)

        self.averages = 1
        self.target_frequency = 100e6

    @property
    def averages(self):
        """The number of averages used for the simulation.

        More averages improve the signal-to-noise ratio of the simulated signal.
        """
        return self._averages

    @averages.setter
    def averages(self, value):
        self._averages = value

    @property
    def target_frequency(self):
        """The target frequency for the simulation.

        Doesn't do anything at the moment.
        """
        return self._target_frequency

    @target_frequency.setter
    def target_frequency(self, value):
        self._target_frequency = value
