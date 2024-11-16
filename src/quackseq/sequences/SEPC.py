"""A spin echo sequence with phase cycling."""

from quackseq.pulsesequence import QuackSequence
from quackseq.functions import RectFunction


def create_SEPC() -> QuackSequence:
    """Creates a simple spin echo sequence with phase cycling.
    
    The sequence consists of a pi/2 pulse, a pi pulse, and a readout event.

    The phase cycling is set to cycle through 0°, 90°, 180°, 270° for the first pulse and constant 180° for the second pulse.
    The readout phase for the different phase cycles is set to 0°, 90°, 180°, 270°.

    Returns:
        QuackSequence: The SEPC sequence
    """
    sepc = QuackSequence("SEPC")
    sepc.add_pulse_event("pi-half", "3u", 100, 0, RectFunction())
    # This causes the phase to cycle through 0, 90, 180, 270
    sepc.set_tx_n_phase_cycles("pi-half", 4)

    sepc.add_blank_event("te-half", "150u")
    # For the second pulse we just need a phase of 180
    sepc.add_pulse_event("pi", "6u", 100, 180, RectFunction())
    sepc.add_blank_event("blank", "50u")

    sepc.add_readout_event("rx", "200u")
    # Readout scheme for phase cycling TX pulses have the scheme 0 90 180 270 
    readout_scheme = [0, 90, 180, 270]

    sepc.set_rx_phase("rx", readout_scheme)

    return sepc
