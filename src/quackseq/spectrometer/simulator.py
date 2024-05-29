from quackseq.spectrometer.spectrometer import Spectrometer

from .simulator_model import SimulatorModel
from .simulator_controller import SimulatorController

class Simulator(Spectrometer):

    def __init__(self):
        self.model = SimulatorModel()
        self.controller = SimulatorController(self.model)

    def run_sequence(self, sequence):
        result =self.controller.run_sequence(sequence)
        return result

    def set_averages(self, value: int):
        self.model.average = value