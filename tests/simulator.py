# Dummy test to communicate the structure
from quackseq.pulsesequence import PulseSequence
from quackseq.event import Event
from quackseq.functions import RectFunction


seq = PulseSequence("test")

tx = Event("tx", "10u")

# tx.set_tx_amplitude(1)
#tx.set_tx_phase(0)
#tx.set_shape(RectFunction())

#seq.add_event(tx)

#blank = Event("blank", "10u")

#seq.add_event(blank)

#rx = Event("rx", "10u")
#rx.set_rx_phase(0)
#rx.set_rx(True)

#seq.add_event(rx)

#TR = Event("TR", "1ms")

#seq.add_event(TR)

#sim = Simulator()

#sim.set_averages(100)

# Returns the data at the  RX event
#result = sim.run(seq)

#result.plot()
