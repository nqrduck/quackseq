"""The base class for the spectrometer used in quackseq. This class is just a skeleton and should be inherited by all spectrometer implementations."""


class Spectrometer:
    """Base class for spectrometers.

    This class should be inherited by all spectrometers.
    The spectrometers then need to implement the methods of this class.
    """

    def run_sequence(self, sequence):
        """Starts the measurement.

        This method should be called when the measurement is started.
        """
        raise NotImplementedError

    def set_frequency(self, value: float):
        """Sets the frequency of the spectrometer."""
        raise NotImplementedError

    def set_averages(self, value: int):
        """Sets the number of averages."""
        raise NotImplementedError
