"""A simple SE sequence with a pi/2 pulse, a pi pulse, and a readout event."""

from quackseq.pulsesequence import QuackSequence
from quackseq.functions import RectFunction

def create_SE() -> QuackSequence:
    """Creates a simple SE sequence with a pi/2 pulse, a pi pulse, and a readout event.
    
    Returns:
        QuackSequence: The SE sequence
    """
    SE = QuackSequence("SE")
    SE.add_pulse_event("pi-half", "3u", 100, 0, RectFunction())
    SE.add_blank_event("te-half", "150u")
    SE.add_pulse_event("pi", "6u", 100, 0, RectFunction())
    SE.add_blank_event("blank", "50u")
    SE.add_readout_event("rx", "200u")

    return SE