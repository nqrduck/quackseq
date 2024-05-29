import unittest
import logging
import matplotlib.pyplot as plt
from quackseq.pulsesequence import QuackSequence
from quackseq.event import Event
from quackseq.functions import RectFunction
from quackseq.spectrometer.simulator import Simulator

# logging.basicConfig(level=logging.DEBUG)


class TestQuackSequence(unittest.TestCase):

    def test_event_creation(self):
        seq = QuackSequence("test - event creation")
        seq.add_pulse_event("tx", "10u", 1, 0, RectFunction())
        seq.add_blank_event("blank", "3u")
        seq.add_readout_event("rx", "100u")
        seq.add_blank_event("TR", "1m")

        json = seq.to_json()
        print(json)

        sim = Simulator()
        sim.set_averages(100)

        result = sim.run_sequence(seq)
        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, "tdx"))
        self.assertTrue(hasattr(result, "tdy"))
        self.assertGreater(len(result.tdx), 0)
        self.assertGreater(len(result.tdy), 0)

        # Plotting the result can be useful for visual inspection during development
        plt.plot(result.tdx, abs(result.tdy))
        plt.show()

    def test_simulation_run_sequence(self):
        seq = QuackSequence("test - simulation run sequence")

        tx = Event("tx", "10u", seq)
        seq.add_event(tx)
        seq.set_tx_amplitude(tx, 1)
        seq.set_tx_phase(tx, 0)

        json = seq.to_json()
        print(json)

        rect = RectFunction()
        seq.set_tx_shape(tx, rect)

        blank = Event("blank", "3u", seq)
        seq.add_event(blank)

        rx = Event("rx", "100u", seq)
        seq.set_rx(rx, True)
        seq.add_event(rx)

        TR = Event("TR", "1m", seq)
        seq.add_event(TR)

        sim = Simulator()
        sim.set_averages(100)

        result = sim.run_sequence(seq)
        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, "tdx"))
        self.assertTrue(hasattr(result, "tdy"))
        self.assertGreater(len(result.tdx), 0)
        self.assertGreater(len(result.tdy), 0)

        # Plotting the result can be useful for visual inspection during development
        plt.plot(result.tdx, abs(result.tdy))
        plt.show()


if __name__ == "__main__":
    unittest.main()
