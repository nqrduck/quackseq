"""Settings for the different spectrometers."""

import logging

logger = logging.getLogger(__name__)


class Setting:
    """A setting for the spectrometer is a value that is the same for all events in a pulse sequence.

    E.g. the Transmit gain or the number of points in a spectrum.

    Args:
        name (str) : The name of the setting as it is used in the code
        category (str) : The category of the setting
        description (str) : A description of the setting
        default : The default value of the setting

    Attributes:
        name (str) : The name of the setting
        category (str) : The category of the setting
        description (str) : A description of the setting
        value : The value of the setting
        category (str) : The category of the setting
    """

    def __init__(
        self, name: str, category: str, description: str = None, default=None
    ) -> None:
        """Create a new setting.

        Args:
            name (str): The name of the setting.
            category (str): The category of the setting.
            description (str): A description of the setting.
            default: The default value of the setting.
        """
        self.name = name
        self.category = category
        self.description = description
        self.default = default
        if default is not None:
            self.value = default
            # Update the description with the default value
            self.description += f"\n (Default: {default})"


class NumericalSetting(Setting):
    """A setting that is a numerical value.

    It can additionally have a minimum and maximum value.
    """

    def __init__(
        self,
        name: str,
        category: str,
        description: str,
        default,
        min_value=None,
        max_value=None,
    ) -> None:
        """Create a new numerical setting."""
        super().__init__(
            name,
            category,
            self.description_limit_info(description, min_value, max_value),
            default,
        )
        self.min_value = min_value
        self.max_value = max_value

    def description_limit_info(self, description: str, min_value, max_value) -> str:
        """Updates the description with the limits of the setting if there are any.

        Args:
            description (str): The description of the setting.
            min_value: The minimum value of the setting.
            max_value: The maximum value of the setting.

        Returns:
            str: The description of the setting with the limits.
        """
        if min_value is not None and max_value is not None:
            description += f"\n (min: {min_value}, max: {max_value})"
        elif min_value is not None:
            description += f"\n (min: {min_value})"
        elif max_value is not None:
            description += f"\n (max: {max_value})"

        return description


class FloatSetting(NumericalSetting):
    """A setting that is a Float.

    Args:
        name (str) : The name of the setting
        category (str) : The category of the setting
        default : The default value of the setting
        description (str) : A description of the setting
        min_value : The minimum value of the setting
        max_value : The maximum value of the setting
        slider : If the setting should be displayed as a slider (only in the GUI not used in this GUI)
        suffix : The suffix that is added to the value of the QSpinBox
    """

    DEFAULT_LENGTH = 100

    def __init__(
        self,
        name: str,
        category: str,
        default: float,
        description: str,
        min_value: float = None,
        max_value: float = None,
        slider=False,
        suffix="",
    ) -> None:
        """Create a new float setting."""
        super().__init__(name, category, description, default, min_value, max_value)
        self.slider = slider
        self.suffix = suffix

    @property
    def value(self):
        """The value of the setting. In this case, a float."""
        return self._value

    @value.setter
    def value(self, value):
        logger.debug(f"Setting {self.name} to {value}")
        self._value = float(value)


class IntSetting(NumericalSetting):
    """A setting that is an Integer.

    Args:
        name (str) : The name of the setting
        category (str) : The category of the setting
        default : The default value of the setting
        description (str) : A description of the setting
        min_value : The minimum value of the setting
        max_value : The maximum value of the setting
        slider : If the setting should be displayed as a slider (only in the GUI not used in this GUI)
        suffix : The suffix that is added to the value of the QSpinBox
        scientific_notation : If the value should be displayed in scientific notation
    """

    def __init__(
        self,
        name: str,
        category: str,
        default: int,
        description: str,
        min_value=None,
        max_value=None,
        slider=False,
        suffix="",
        scientific_notation=False,
    ) -> None:
        """Create a new int setting."""
        super().__init__(name, category, description, default, min_value, max_value)
        self.slider = slider
        self.suffix = suffix
        self.scientific_notation = scientific_notation

    @property
    def value(self):
        """The value of the setting. In this case, an int."""
        return self._value

    @value.setter
    def value(self, value):
        logger.debug(f"Setting {self.name} to {value}")
        value = int(float(value))

        self._value = value


class BooleanSetting(Setting):
    """A setting that is a Boolean.

    Args:
        name (str) : The name of the setting
        category (str) : The category of the setting
        default : The default value of the setting
        description (str) : A description of the setting
    """

    def __init__(
        self, name: str, category: str, default: bool, description: str
    ) -> None:
        """Create a new boolean setting."""
        super().__init__(name, category, description, default)

    @property
    def value(self):
        """The value of the setting. In this case, a bool."""
        return self._value

    @value.setter
    def value(self, value):
        try:
            logger.debug(f"Setting {self.name} to {value}")
            self._value = bool(value)
        except ValueError:
            raise ValueError("Value must be a bool")


class SelectionSetting(Setting):
    """A setting that is a selection from a list of options.

    Args:
        name (str) : The name of the setting
        category (str) : The category of the setting
        options (list) : A list of options to choose from
        default : The default value of the setting
        description (str) : A description of the setting
    """

    def __init__(
        self, name: str, category: str, options: list, default: str, description: str
    ) -> None:
        """Create a new selection setting."""
        if default not in options:
            raise ValueError("Default value must be one of the options")

        self.options = options

        super().__init__(name, category, description, default)

    @property
    def value(self):
        """The value of the setting. In this case, a string."""
        return self._value

    @value.setter
    def value(self, value):

        if value in self.options:
            logger.debug(f"Setting {self.name} to {value}")
            self._value = value
        else:
            raise ValueError(f"Value must be one of the options {self.options}")


class StringSetting(Setting):
    """A setting that is a string.

    Args:
        name (str) : The name of the setting
        category (str) : The category of the setting
        default : The default value of the setting
        description (str) : A description of the setting
    """

    def __init__(
        self, name: str, category: str, default: str, description: str
    ) -> None:
        """Create a new string setting."""
        super().__init__(name, category, description, default)

    @property
    def value(self):
        """The value of the setting. In this case, a string."""
        return self._value

    @value.setter
    def value(self, value):
        try:
            logger.debug(f"Setting {self.name} to {value}")
            self._value = str(value)
        except ValueError:
            raise ValueError("Value must be a string")
