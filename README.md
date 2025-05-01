# QuackSeq

QuackSeq is a tool for programming pulse sequences for magnetic resonance experiments.

The general  idea  is that different QuackSeq sequences can be run on either hardware spectrometers or software simulators.

Different QuackSeq interpreters can be used to run the same sequence on different spectrometers or simulators.

## Installation

Create a new virtual environment and install QuackSeq:

```bash
python3 -m venv venv
source venv/bin/activate
pip install quackseq
```

## Modules

- [quackseq-simulator](https://git.private.coffee/nqrduck/quackseq-simulator): A simulator for QuackSeq sequences.
- [quackseq-limenqr](https://git.private.coffee/nqrduck/quackseq-limenqr): A QuackSeq interpreter for the LimeNQR spectrometer.
