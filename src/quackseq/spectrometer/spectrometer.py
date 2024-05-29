class Spectrometer():
    """Base class for spectrometers.

    This class should be inherited by all spectrometers.
    The spectrometers then need to implement the methods of this class.
    """

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
    
    @property
    def controller(self):
        """The controller of the spectrometer."""
        return self._controller
    
    @controller.setter
    def controller(self, controller):
        self._controller = controller

    @property
    def model(self):
        """The model of the spectrometer."""
        return self._model
    
    @model.setter
    def model(self, model):
        self._model = model