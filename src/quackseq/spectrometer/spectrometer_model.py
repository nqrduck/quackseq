"""The base class for all spectrometer models."""

import logging
from collections import OrderedDict
from quackseq.spectrometer.spectrometer_setting import Setting

logger = logging.getLogger(__name__)


class SpectrometerModel():
    """The base class for all spectrometer models.

    It contains the settings and pulse parameters of the spectrometer.

    Args:
        module (Module) : The module that the spectrometer is connected to

    Attributes:
        settings (OrderedDict) : The settings of the spectrometer
        pulse_parameter_options (OrderedDict) : The pulse parameter options of the spectrometer
    """

    settings: OrderedDict
    pulse_parameter_options: OrderedDict

    def __init__(self, module):
        """Initializes the spectrometer model.

        Args:
            module (Module) : The module that the spectrometer is connected to
        """
        super().__init__(module)
        self.settings = OrderedDict()
        self.pulse_parameter_options = OrderedDict()

    def add_setting(self, setting: Setting, category: str) -> None:
        """Adds a setting to the spectrometer.

        Args:
            setting (Setting) : The setting to add
            category (str) : The category of the setting
        """
        if category not in self.settings.keys():
            self.settings[category] = []
        self.settings[category].append(setting)

    def get_setting_by_name(self, name: str) -> Setting:
        """Gets a setting by its name.

        Args:
            name (str) : The name of the setting

        Returns:
            Setting : The setting with the specified name

        Raises:
            ValueError : If no setting with the specified name is found
        """
        for category in self.settings.keys():
            for setting in self.settings[category]:
                if setting.name == name:
                    return setting
        raise ValueError(f"Setting with name {name} not found")

    def add_pulse_parameter_option(
        self, name: str, pulse_parameter_class: "PulseParameter"
    ) -> None:
        """Adds a pulse parameter option to the spectrometer.

        Args:
            name (str) : The name of the pulse parameter
            pulse_parameter_class (PulseParameter) : The pulse parameter class
        """
        self.pulse_parameter_options[name] = pulse_parameter_class

    @property
    def target_frequency(self):
        """The target frequency of the spectrometer in Hz. This is the frequency where the magnetic resonance experiment is performed."""
        raise NotImplementedError

    @target_frequency.setter
    def target_frequency(self, value):
        raise NotImplementedError

    @property
    def averages(self):
        """The number of averages for the spectrometer."""
        raise NotImplementedError

    @averages.setter
    def averages(self, value):
        raise NotImplementedError
