"""This module defines the measurement data structure and the fit class for measurement data."""

import logging
import numpy as np
from scipy.optimize import curve_fit
from numpy.fft import ifft, fft

from quackseq.functions import Function
from quackseq.signalprocessing import SignalProcessing as sp

logger = logging.getLogger(__name__)


class Measurement:
    """This class defines how measurement data should look.

    It includes pulse parameters necessary for further signal processing.
    Every spectrometer should adhere to this data structure in order to be compatible with the rest of the nqrduck.

    Args:
        name (str): Name of the measurement.
        tdx (np.array): Time axis for the x axis of the measurement data.
        tdy (np.array): Time axis for the y axis of the measurement data. This can be multi-dimensional. Axis 0 are the different data sets (e.g. phase cycles).
        target_frequency (float): Target frequency of the measurement.
        frequency_shift (float, optional): Frequency shift of the measurement. Defaults to 0.
        IF_frequency (float, optional): Intermediate frequency of the measurement. Defaults to 0.

    Attributes:
        tdx (np.array): Time axis for the x axis of the measurement data. Axis 0 are the different data sets (e.g. phase cycles).
        tdy (np.array): Time axis for the y axis of the measurement data. Axis 0 are the different data sets (e.g. phase cycles).
        target_frequency (float): Target frequency of the measurement.
        frequency_shift (float): Frequency shift of the measurement.
        IF_frequency (float): Intermediate frequency of the measurement.
        fdx (np.array): Frequency axis for the x axis of the measurement data.
        fdy (np.array): Frequency axis for the y axis of the measurement data.
    """

    def __init__(
        self,
        name: str,
        tdx: np.array,
        tdy: np.array,
        target_frequency: float,
        frequency_shift: float = 0,
        IF_frequency: float = 0,
    ) -> None:
        """Initializes the measurement."""
        self.name = name
        self.tdx = tdx
        #If tdy has no empty second dimension, add one
        if len(tdy.shape) == 1:
            tdy = np.expand_dims(tdy, axis=1)
        self.tdy = tdy
        self.target_frequency = target_frequency
        self.frequency_shift = frequency_shift
        self.IF_frequency = IF_frequency
        if tdx is not None and tdy is not None and tdx.size > 0 and tdy.size > 0:
            fdx, fdy = sp.fft(tdx, tdy, frequency_shift)
            self.fdx = fdx
            self.fdy = fdy
        else:
            self.fdx = None
            self.fdy = None

        self.fits = []

    def add_dataset(self, tdy: np.array) -> None:
        """Adds dataset to the measurement. We only add the y data, as the x data is the same for all datasets.

        Args:
            tdy (np.array): Time axis for the y axis of the measurement data.
        """
        # Add the y data in the second dimension
        self.tdy = np.concatenate((self.tdy, tdy), axis=1)
        _, fdy = sp.fft(self.tdx, tdy, self.frequency_shift)
        self.fdy = np.concatenate((self.fdy, fdy), axis=1)

    def apodization(self, function: Function) -> "Measurement":
        """Applies apodization to the measurement data.

        Args:
            function (Function): Apodization function.

        Returns:
            Measurement: The apodized measurement.
        """
        duration = (self.tdx[-1] - self.tdx[0]) * 1e-6
        resolution = duration / len(self.tdx)
        logger.debug("Resolution: %s", resolution)

        y_weight = function.get_pulse_amplitude(duration, resolution)

        apodized_measurement = Measurement(
            self.name,
            self.tdx,
            self.tdy[:, 0] * y_weight,
            target_frequency=self.target_frequency,
            IF_frequency=self.IF_frequency,
        )

        # Apply the apodization function to the y data skip the first column
        for i in range(1, self.tdy.shape[1]):
            apodized_measurement.add_dataset(self.tdy[:, i] * y_weight)

        logger.debug(f"Shape of tdy after apodization: {apodized_measurement.tdy.shape}")

        return apodized_measurement

    def phase_shift(self, phase: float, index: int, axis=0) -> np.array:
        """Applies a phase shift to the measurement data.

        Args:
            phase (float): Phase shift in degrees.
            index (int): Index of the data set to apply the phase shift to.
            axis (int): Axis to apply the phase shift to. Defaults to 0.
        """
        spec = fft(self.tdy[:, index])
        shifted_signal = np.exp(1j * np.deg2rad(phase)) * spec

        self.tdy[:, index] = ifft(shifted_signal, n=len(self.tdy[:, index]))

    def add_fit(self, fit: "Fit") -> None:
        """Adds a fit to the measurement.

        Args:
            fit (Fit): The fit to add.
        """
        self.fits.append(fit)

    def delete_fit(self, fit: "Fit") -> None:
        """Deletes a fit from the measurement.

        Args:
            fit (Fit): The fit to delete.
        """
        self.fits.remove(fit)

    def edit_fit_name(self, fit: "Fit", name: str) -> None:
        """Edits the name of a fit.

        Args:
            fit (Fit): The fit to edit.
            name (str): The new name.
        """
        logger.debug(f"Editing fit name to {name}.")
        fit.name = name

    def to_json(self) -> dict:
        """Converts the measurement to a JSON-compatible format.

        Returns:
            dict: The measurement in JSON-compatible format.
        """
        return {
            "name": self.name,
            "tdx": self.tdx.tolist(),
            "tdy": self.serialize_complex_array(self.tdy),
            "target_frequency": self.target_frequency,
            "IF_frequency": self.IF_frequency,
            "fits": [fit.to_json() for fit in self.fits],
        }

    @classmethod
    def from_json(cls, json: dict) -> "Measurement":
        """Converts the JSON format to a measurement.

        Args:
            json (dict): The measurement in JSON-compatible format.

        Returns:
            Measurement: The measurement.
        """
        tdy = np.array(json["tdy"][0]) + 1j * np.array(json["tdy"][1])

        measurement = cls(
            json["name"],
            np.array(json["tdx"]),
            tdy,
            target_frequency=json["target_frequency"],
            IF_frequency=json["IF_frequency"],
        )

        for fit_json in json["fits"]:
            measurement.add_fit(Fit.from_json(fit_json, measurement))

        return measurement

    def serialize_complex_array(self, array: np.array) -> list:
        """Serializes a complex array to a list.

        Args:
            array (np.array): The complex array.

        Returns:
            list: The serialized complex array.
        """
        return [array.real.tolist(), array.imag.tolist()]

    # Properties for encapsulation
    @property
    def name(self) -> str:
        """Name of the measurement."""
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = value

    @property
    def tdx(self) -> np.array:
        """Time domain data for the measurement (x)."""
        return self._tdx

    @tdx.setter
    def tdx(self, value: np.array) -> None:
        self._tdx = value

    @property
    def tdy(self) -> np.array:
        """Time domain data for the measurement (y)."""
        return self._tdy

    @tdy.setter
    def tdy(self, value: np.array) -> None:
        self._tdy = value

    @property
    def fdx(self) -> np.array:
        """Frequency domain data for the measurement (x)."""
        return self._fdx

    @fdx.setter
    def fdx(self, value: np.array) -> None:
        self._fdx = value

    @property
    def fdy(self) -> np.array:
        """Frequency domain data for the measurement (y)."""
        return self._fdy

    @fdy.setter
    def fdy(self, value: np.array) -> None:
        self._fdy = value

    @property
    def target_frequency(self) -> float:
        """Target frequency of the measurement."""
        return self._target_frequency

    @target_frequency.setter
    def target_frequency(self, value: float) -> None:
        self._target_frequency = value

    @property
    def fits(self) -> list:
        """Fits of the measurement."""
        return self._fits

    @fits.setter
    def fits(self, value: list) -> None:
        self._fits = value


class MeasurementError(Measurement):
    """This will be returned if the measurement is not valid."""

    def __init__(self, name: str, error_meassage: str):
        """Initializes the error message."""
        super().__init__(name, None, None, 0)
        self.error_message = error_meassage


class Fit:
    """The fit class for measurement data. A fit can be performed on either the frequency or time domain data.

    A measurement can have multiple fits.
    """

    subclasses = []

    def __init_subclass__(cls, **kwargs) -> None:
        """Adds the subclass to the list of subclasses."""
        super().__init_subclass__(**kwargs)
        cls.subclasses.append(cls)

    def __init__(self, name: str, domain: str, measurement: Measurement) -> None:
        """Initializes the fit."""
        self.name = name
        self.domain = domain
        self.measurement = measurement
        self.fit()

    def fit(self) -> None:
        """Fits the measurement data and sets the fit parameters and covariance."""
        if self.domain == "time":
            x = self.measurement.tdx
            # For multi-dimensional data, we take the last data set
            y = self.measurement.tdy[:, -1]
        elif self.domain == "frequency":
            x = self.measurement.fdx
            y = self.measurement.fdy[:, -1]
        else:
            raise ValueError("Domain not recognized.")

        initial_guess = self.initial_guess()
        self.parameters, self.covariance = curve_fit(
            self.fit_function, x, abs(y), p0=initial_guess
        )

        self.x = x
        self.y = self.fit_function(x, *self.parameters)

    def fit_function(self, x: np.array, *parameters) -> np.array:
        """The fit function.

        Args:
            x (np.array): The x data.
            *parameters: The fit parameters.

        Returns:
            np.array: The y data.
        """
        raise NotImplementedError

    def initial_guess(self) -> list:
        """Initial guess for the fit.

        Returns:
            list: The initial guess.
        """
        raise NotImplementedError

    def to_json(self) -> dict:
        """Converts the fit to a JSON-compatible format.

        Returns:
            dict: The fit in JSON-compatible format.
        """
        return {
            "name": self.name,
            "class": self.__class__.__name__,
        }

    @classmethod
    def from_json(cls, data: dict, measurement: Measurement) -> "Fit":
        """Converts the JSON format to a fit.

        Args:
            data (dict): The fit in JSON-compatible format.
            measurement (Measurement): The measurement.

        Returns:
            Fit: The fit.
        """
        for subclass in cls.subclasses:
            if subclass.__name__ == data["class"]:
                return subclass(name=data["name"], measurement=measurement)

        raise ValueError(f"Subclass {data['class']} not found.")

    @property
    def x(self) -> np.array:
        """The x data of the fit."""
        return self._x

    @x.setter
    def x(self, value: np.array) -> None:
        self._x = value

    @property
    def y(self) -> np.array:
        """The y data of the fit."""
        return self._y

    @y.setter
    def y(self, value: np.array) -> None:
        self._y = value


class T2StarFit(Fit):
    """T2* fit for measurement data."""

    def __init__(self, measurement: Measurement, name: str = "T2*") -> None:
        """Initializes the T2* fit."""
        super().__init__(name, "time", measurement)

    def fit(self) -> None:
        """Fits the measurement data and sets the fit parameters and covariance."""
        super().fit()
        self.parameters = {
            "S0": self.parameters[0],
            "T2Star": self.parameters[1],
            "covariance": self.covariance,
        }

    def fit_function(self, t: np.array, S0: float, T2Star: float) -> np.array:
        """The T2* fit function used for curve fitting."""
        return S0 * np.exp(-t / T2Star)

    def initial_guess(self) -> list:
        """Initial guess for the T2* fit."""
        return [1, 1]


class LorentzianFit(Fit):
    """Lorentzian fit for measurement data."""

    def __init__(self, measurement: Measurement, name: str = "Lorentzian") -> None:
        """Initializes the Lorentzian fit."""
        super().__init__(name, "frequency", measurement)

    def fit(self) -> None:
        """Fits the measurement data and sets the fit parameters and covariance."""
        super().fit()
        self.parameters = {
            "S0": self.parameters[0],
            "T2Star": self.parameters[1],
            "covariance": self.covariance,
        }
        logger.debug("Lorentzian fit parameters: %s", self.parameters)

    def fit_function(self, f: np.array, S0: float, T2Star: float) -> np.array:
        """The Lorentzian fit function used for curve fitting."""
        return S0 / (1 + (2 * np.pi * f * T2Star) ** 2)

    def initial_guess(self) -> list:
        """Initial guess for the Lorentzian fit."""
        return [1, 1]
