"""Composite FID example.

This example demonstrates how to simulate a composite FID signal using the quackseq simulator.

See the paper:
Sauer, K.L., Klug, C.A., Miller, J.B. et al. Using quaternions to design composite pulses for spin-1 NQR. Appl. Magn. Reson. 25, 485–500 (2004). https://doi.org/10.1007/BF03166543

This also works for Samples with spin > 1.
"""

from quackseq.pulsesequence import QuackSequence
from quackseq.functions import RectFunction


def create_COMPFID():
    """Creates a composite FID sequence."""
    COMPFID = QuackSequence("COMPFID")
    COMPFID.add_pulse_event("tx1", "3u", 100, 0, RectFunction())
    COMPFID.add_pulse_event("tx2", "6u", 100, 45, RectFunction())
    # This makes the phase 45, 135, 225, 315 (because of the previous 45 degree phase shift and 360/4 = 90 degree phase shift)
    COMPFID.set_tx_n_phase_cycles("tx2", 4)
    COMPFID.add_blank_event("blank", "5u")

    COMPFID.add_readout_event("rx", "100u")

    # No phase shifiting of the receive data but weighting of -1 for the 45 degree pulse, +1 for the 135 degree pulse, -1 for the 225 degree pulse and +1 for the 315 degree pulse
    readout_scheme = [0, 180, 0, 180]

    COMPFID.set_rx_phase("rx", readout_scheme)

    return COMPFID
