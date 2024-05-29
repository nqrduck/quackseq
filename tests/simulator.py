# Dummy test to communicate the structure
import logging
import matplotlib.pyplot as plt

from quackseq.pulsesequence import QuackSequence
from quackseq.event import Event
from quackseq.functions import RectFunction
from quackseq.spectrometer.simulator import Simulator

logging.basicConfig(level=logging.DEBUG)

seq = QuackSequence("test")

tx = Event("tx", "10u", seq)

seq.add_event(tx)

seq.set_tx_amplitude(tx, 1)
seq.set_tx_phase(tx, 0)

rect = RectFunction()

seq.set_tx_shape(tx, rect)

blank = Event("blank", "3u", seq)

seq.add_event(blank)

rx = Event("rx", "50u", seq)
#rx.set_rx_phase(0)

seq.set_rx(rx, True)

seq.add_event(rx)

TR = Event("TR", "1m", seq)

seq.add_event(TR)

json = seq.to_json()

print(json)

sim = Simulator()

sim.set_averages(100)

# Returns the data at the  RX event
result = sim.run_sequence(seq)

plt.plot(result.tdx, abs(result.tdy))
plt.show()
