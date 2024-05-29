"""The base class for all spectrometer models."""

import logging
from collections import OrderedDict
from typing import Any
from quackseq.spectrometer.spectrometer_settings import Setting

logger = logging.getLogger(__name__)

class QuackSettings(OrderedDict):
    def __getattr__(self, key):
        return self[key].value

    def __setattr__(self, key, value):
        self[key].value = value

    @property
    def categories(self):
        categories = []

        for setting in self.values():
            if not setting.category in categories:
                categories.append(setting.category)

        return categories
        
    def get_settings_by_category(self, category):
        settings = []

        for setting in self.values():
            if setting.category == category:
                settings.append(setting)

        return settings

class SpectrometerModel():
    """The base class for all spectrometer models.

    It contains the settings and pulse parameters of the spectrometer.

    Attributes:
        settings (QuackSettings) : The settings of the spectrometer
    """

    settings: QuackSettings

    def __init__(self):
        """Initializes the spectrometer model."""
        self.settings = QuackSettings()


    def add_setting(self,name: str, setting: Setting) -> None:
        """Adds a setting to the spectrometer.

        Args:
            name (str) : The name of the setting as it should  be  used in the code
            setting (Setting) : The setting to add
        """
        self.settings[name] = setting

    def get_setting_by_name(self, name: str) -> Setting:
        """Gets a setting by its name.

        Args:
            name (str) : The name of the setting as it is used in the code

        Returns:
            Setting : The setting with the specified name

        Raises:
            ValueError : If no setting with the specified name is found
        """
        if name in self.settings:
            return self.settings[name]
        
        raise ValueError(f"No setting with name {name} found")
    
    def get_setting_by_display_name(self, display_name : str) -> Setting:
        """Gets a setting by its display name.

        Args:
            display_name (str) : The display name of the setting

        Returns:
            Setting : The setting with the specified display name

        Raises:
            ValueError : If no setting with the specified display name is found
        """
        for setting in self.settings.values():
            if setting.name == display_name:
                return setting

        raise ValueError(f"No setting with display name {display_name} found")
    
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
