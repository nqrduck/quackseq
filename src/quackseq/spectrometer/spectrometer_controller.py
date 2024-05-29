"""Base class for all spectrometer controllers."""

class SpectrometerController():
    """The base class for all spectrometer controllers."""

    def run_sequence(self, sequence):
        """Starts the measurement.

        This method should be called when the measurement is started.
        """
        raise NotImplementedError

    def set_frequency(self, value : float):
        """Sets the frequency of the spectrometer."""
        raise NotImplementedError

    def set_averages(self, value : int):
        """Sets the number of averages."""
        raise NotImplementedError
