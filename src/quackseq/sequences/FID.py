"""Simple FID sequence with a single excitation pulse and readout event."""

from quackseq.pulsesequence import QuackSequence
from quackseq.functions import RectFunction

def create_FID() -> QuackSequence:
    """Creates a simple FID sequence with a single excitation pulse and readout event.
    
    Returns:
        QuackSequence: The FID sequence
    """
    FID = QuackSequence("FID")
    FID.add_pulse_event("tx", "3u", 100, 0, RectFunction())
    FID.add_blank_event("blank", "5u")
    FID.add_readout_event("rx", "100u")
    FID.add_blank_event("TR", "1m")

    return FID