"""Options for the pulse parameters. Options can be of different types, for example boolean, numeric or function. Generally pulse parameters have different values for the different events in a pulse sequence."""

import logging
from quackseq.functions import Function

logger = logging.getLogger(__name__)


class Option:
    """Defines options for the pulse parameters which can then be set accordingly.

    Options can be of different types, for example boolean, numeric or function.

    Args:
        name (str): The name of the option.
        value: The value of the option.

    Attributes:
        name (str): The name of the option.
        value: The value of the option.
    """

    subclasses = []

    def __init_subclass__(cls, **kwargs):
        """Adds the subclass to the list of subclasses."""
        super().__init_subclass__(**kwargs)
        cls.subclasses.append(cls)

    def __init__(self, name: str, value) -> None:
        """Initializes the option."""
        self.name = name
        self.value = value

    def set_value(self):
        """Sets the value of the option.

        This method has to be implemented in the derived classes.
        """
        raise NotImplementedError

    def to_json(self):
        """Returns a json representation of the option.

        Returns:
            dict: The json representation of the option.
        """
        return {
            "name": self.name,
            "value": self.value,
            "class": self.__class__.__name__,
        }

    @classmethod
    def from_json(cls, data) -> "Option":
        """Creates an option from a json representation.

        Args:
            data (dict): The json representation of the option.

        Returns:
            Option: The option.
        """
        for subclass in cls.subclasses:
            logger.debug(f"Keys data: {data.keys()}")
            if subclass.__name__ == data["class"]:
                cls = subclass
                break

        # Check if from_json is implemented for the subclass
        if cls.from_json.__func__ == Option.from_json.__func__:
            obj = cls(data["name"], data["value"])
        else:
            obj = cls.from_json(data)

        return obj


class BooleanOption(Option):
    """Defines a boolean option for a pulse parameter option."""

    def set_value(self, value):
        """Sets the value of the option."""
        self.value = value
        self.value_changed.emit()


class NumericOption(Option):
    """Defines a numeric option for a pulse parameter option."""

    def __init__(
        self,
        name: str,
        value,
        is_float=True,
        min_value=None,
        max_value=None,
        slider=False,
    ) -> None:
        """Initializes the NumericOption.

        Args:
            name (str): The name of the option.
            value: The value of the option.
            is_float (bool): If the value is a float.
            min_value: The minimum value of the option.
            max_value: The maximum value of the option.
            slider (bool): If the option should be displayed as a slider. This is not used for the pulseq module, but visualizations can use this information.
        """
        super().__init__(name, value)
        self.is_float = is_float
        self.min_value = min_value
        self.max_value = max_value
        self.slider = slider

    def set_value(self, value):
        """Sets the value of the option."""
        if value < self.min_value:
            self.value = self.min_value
            self.value_changed.emit()
        elif value >= self.max_value:
            self.value = self.max_value
            self.value_changed.emit()
        else:
            raise ValueError(
                f"Value {value} is not in the range of {self.min_value} to {self.max_value}. This should have been caught earlier."
            )

    def to_json(self):
        """Returns a json representation of the option.

        Returns:
            dict: The json representation of the option.
        """
        return {
            "name": self.name,
            "value": self.value,
            "class": self.__class__.__name__,
            "is_float": self.is_float,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "slider": self.slider,
        }

    @classmethod
    def from_json(cls, data):
        """Creates a NumericOption from a json representation.

        Args:
            data (dict): The json representation of the NumericOption.

        Returns:
            NumericOption: The NumericOption.
        """
        obj = cls(
            data["name"],
            data["value"],
            is_float=data["is_float"],
            min_value=data["min_value"],
            max_value=data["max_value"],
        )
        return obj


class FunctionOption(Option):
    """Defines a selection option for a pulse parameter option.

    It takes different function objects.

    Args:
        name (str): The name of the option.
        functions (list): The functions that can be selected.

    Attributes:
        name (str): The name of the option.
        functions (list): The functions that can be selected.
    """

    def __init__(self, name, functions) -> None:
        """Initializes the FunctionOption."""
        super().__init__(name, functions[0])
        self.functions = functions

    def set_value(self, value):
        """Sets the value of the option.

        Args:
            value: The value of the option.
        """
        self.value = value

    def get_function_by_name(self, name):
        """Returns the function with the given name.

        Args:
            name (str): The name of the function.

        Returns:
            Function: The function with the given name.
        """
        for function in self.functions:
            if function.name == name:
                return function
        raise ValueError(f"Function with name {name} not found")

    def to_json(self):
        """Returns a json representation of the option.

        Returns:
            dict: The json representation of the option.
        """
        return {
            "name": self.name,
            "value": self.value.to_json(),
            "class": self.__class__.__name__,
            "functions": [function.to_json() for function in self.functions],
        }

    @classmethod
    def from_json(cls, data):
        """Creates a FunctionOption from a json representation.

        Args:
            data (dict): The json representation of the FunctionOption.

        Returns:
            FunctionOption: The FunctionOption.
        """
        logger.debug(f"Data: {data}")
        # These are all available functions
        functions = [Function.from_json(function) for function in data["functions"]]
        obj = cls(data["name"], functions)
        obj.value = Function.from_json(data["value"])
        return obj


class TableOption(Option):
    """A table option has rows and columns and can be used to store a table of values.

    The table option acts as a 'meta' option, which means that we can add different types of options to the table as rows. 
    Associated with every row we can add a number of different values.
    The number  of rows can be adjusted at runtime.
    """

    def __init__(self, name: str, value = None) -> None:
        """Initializes the table option."""
        super().__init__(name, value)

        self.options = []
        self.n_rows = 0

    def set_value(self, value):
        """Sets the value of the option."""
        self.value = value

    def add_option(self, option: Option) -> None:
        """Adds an option to the table.

        Args:
            option (Option): The option to add.
        """
        self.options.append(option)

    def set_n_rows(self, n_rows : int) -> None:
        """Sets the number of rows in the table.

        Args:
            n_rows (int): The number of rows.
        """
        self.n_rows = n_rows

    def to_json(self):
        """Returns a json representation of the option.

        Returns:
            dict: The json representation of the option.
        """
        return {
            "name": self.name,
            "value": self.value,
            "class": self.__class__.__name__,
        }

    @classmethod
    def from_json(cls, data):
        """Creates a TableOption from a json representation.

        Args:
            data (dict): The json representation of the TableOption.

        Returns:
            TableOption: The TableOption.
        """
        obj = cls(data["name"], data["value"])
        return obj


class ReadoutOption(TableOption):
    """Readout Option for Phase Table processing.
    
    The Readout Option is a special TableOption that is used for the processing of phase tables (see phase_table.py).
    The rows are the phase cycles of the sequence.
    
    The columns have two different types of options:
    - NumericOption: The phase value of the phase cycle.
    - FunctionOption: The function that is applied to the phase cycle. Usually this is just +1, -1 or 0.

    """

    def __init__(self) -> None:
        """Initializes the ReadoutOption."""
        super().__init__("Readout Option")

    def set_n_phase_cycles(self, n_phase_cycles: int) -> None:
        """Sets the number of phase cycles in the readout option.

        Args:
            n_phase_cycles (int): The number of phase cycles.
        """
        self.set_n_rows(n_phase_cycles)