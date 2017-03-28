from binary2vec import *
from vec2binary import *
import numpy as np
import binascii

if __name__ == '__main__':
    with open("practice_midi/Native_Faith.mid", 'rb') as f:
        str = f.read()
        hexlify = binascii.hexlify(str)

    midi_ary = [hexlify[i:i + 2].decode('utf-8').upper() for i in range(0, len(hexlify), 2)]

    # ---- parse_midi -----

    midi = MidiParser(midi_ary)
    midi.parse_head()

    midi.parse_truck()
    print("-------header-------")
    print(midi.header)
    print("-------chunk--------")
    print(midi.truck)
    print("--------------------")
    print("-------midi---------")
    midi.parse_data()
    print("--------------------")
    midi.take_true_data()

    track = midi.delta_to_time_order()
    m_obj = Mid2vec(track, midi.header["time_unit"])
    m_obj.midi2vec()
    m_obj.vec2numpy()
    midi_numpy = m_obj.midi_numpy
    midi_T = m_obj.T
    print(midi_numpy)

    #　TODO: tempo,rythm,keyは自動的に抽出できるようにする。

    # ---- decoding_midi -----

    vec2midi = vec2binary(midi.header, midi.truck, midi_numpy, midi_T)
    vec2midi.set_header()
    vec2midi.set_truck()
    vec2midi.numpy2ary()
    vec2midi.ary2dict()
    vec2midi.dict_ary2midi()
    vec2midi.ary2midi_data()
    #print(len(vec2midi.detailed_ary))








