"""Options for the pulse parameters. Options can be of different types, for example boolean, numeric or function. Generally pulse parameters have different values for the different events in a pulse sequence."""

import logging
from collections import OrderedDict
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
            slider (bool): If the option should be displayed as a slider. This is not used for the quackseq module, but visualizations can use this information.
        """
        super().__init__(name, value)
        self.is_float = is_float
        self.min_value = min_value
        self.max_value = max_value
        self.slider = slider

    def set_value(self, value):
        """Sets the value of the option."""
        if self.min_value is None or self.max_value is None:
            self.value = value
            return

        if self.min_value <= value <= self.max_value:
            self.value = value
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

    The table option acts as a 'meta' option, which means that we can add different types of options to the table as columns.
    Associated with every row we can add a number of different values.
    The number  of rows can be adjusted at runtime.
    """

    def __init__(self, name: str, value=None) -> None:
        """Initializes the table option."""
        super().__init__(name, value)

        self.columns = []
        self.n_rows = 0

    def add_column(self, column_name: str, option: Option, default_value) -> None:
        """Adds an option to the table as column.

        Options are added as columns.

        Args:
            option (Option): The class of the option to add.
            column_name (str): The name of the column.
            default_value: The default value of the column.
        """
        column = self.Column(column_name, option, default_value, self.n_rows)
        # Add the column to the table
        self.columns.append(column)

    def set_value(self, values: list) -> None:
        """Sets the value of the option.

        Args:
            values: The values of the different options in the table.
        """
        for i, column in enumerate(values):
            self.columns[i].set_row_values(column)

    def set_column(self, column_name: str, values: list) -> None:
        """Sets the values of a column in the table.

        Args:
            column_name (str): The name of the column.
            values: The values of the column.
        """
        column = self.get_column_by_name(column_name)
        column.set_row_values(values)

    def get_value(self) -> list:
        """Gets the value of the option.

        Returns:
            list: The values of the different options in the table.
        """
        return [column.get_values() for column in self.columns]

    def set_n_rows(self, n_rows: int) -> None:
        """Sets the number of rows in the table.

        Args:
            n_rows (int): The number of rows.
        """
        self.n_rows = n_rows

        # Now we need to set the number of rows for all the options in the table, the last value is repeated if the number of rows is increased
        for column in self.columns:
            column.update_n_rows(n_rows)

    def get_column_by_name(self, name: str) -> Option:
        """Gets an option by its name.

        Args:
            name (str): The name of the option.

        Returns:
            Option: The option with the given name.
        """
        for column in self.columns:
            if column.name == name:
                return column
        raise ValueError(f"Column with name {name} not found")

    def to_json(self):
        """Returns a json representation of the option.

        Returns:
            dict: The json representation of the option.
        """
        return {
            "name": self.name,
            "value": [column.to_json() for column in self.columns],
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
        obj.columns = [cls.Column.from_json(column) for column in data["value"]]
        return obj

    class Column:
        """Defines a column option for a table option.

        Args:
            name (str): The name of the option.
            type (type): The type of the option.
            default_value: The default value of the option.

        """

        def __init__(self, name: str, type, default_value, n_rows: int) -> None:
            """Initializes the column option."""
            self.name = name
            self.type = type
            self.default_value = default_value

            self.options = []
            self.update_n_rows(n_rows)

        def update_n_rows(self, n_rows: int) -> None:
            """Updates the number of rows in the column.

            Args:
                n_rows (int): The number of rows.
            """
            if len(self.options) < n_rows:
                self.options.extend(
                    self.type(self.name, self.default_value)
                    for i in range(n_rows - len(self.options))
                )
            elif len(self.options) > n_rows:
                self.options = self.options[:n_rows]

        def set_row_values(self, values: list) -> None:
            """Sets the values of the options in the column.

            Args:
                values: The values of the options in the column.
            """
            self.update_n_rows(len(values))
            for i, value in enumerate(values):
                self.options[i].set_value(value)

        def get_values(self) -> list:
            """Gets the values of the options in the column.

            Returns:
                list: The values of the options in the column.
            """
            return [option.value for option in self.options]
        
        def to_json(self):
            """Returns a json representation of the column.

            Returns:
                dict: The json representation of the column.
            """
            return {
                "name": self.name,
                "values": [option.to_json() for option in self.options],
            }
        
        @classmethod
        def from_json(cls, data):
            """Creates a Column from a json representation.

            Args:
                data (dict): The json representation of the Column.

            Returns:
                Column: The Column.
            """
            # This needs  to created objects  from the json representation of the options
            logger.debug(f"Data: {data}")
            for subclass in Option.subclasses:
                if subclass.__name__ == data["values"][0]["class"]:
                    type = subclass
                    break

            name = data["name"]
            default_value = data["values"][0]["value"]
            n_rows = len(data["values"])
            logger.debug(f"name: {name}, type: {type}, default_value: {default_value}, n_rows: {n_rows}")
            obj = cls(name, type, default_value, n_rows)

            row_values = [option["value"] for option in data["values"]]
            logger.debug(f"Row values: {row_values}")
            obj.set_row_values(row_values)
            return obj
