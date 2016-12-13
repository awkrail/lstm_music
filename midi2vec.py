import numpy as np
from music21 import *

mf = midi.MidiFile()
mf.open('practice_midi/wind.mid')
mf.read()
s = midi.translate.midiFileToStream(mf)

part = s[0].pitches

print(part)