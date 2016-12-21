from binary2vec import *
import numpy as np
import binascii

if __name__ == '__main__':
    with open("practice_midi/Native_Faith.mid", 'rb') as f:
        str = f.read()
        hexlify = binascii.hexlify(str)

    midi_ary = [hexlify[i:i + 2].decode('utf-8').upper() for i in range(0, len(hexlify), 2)]

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
    # print(track)
    m_obj = Mid2vec(track, midi.header["time_unit"])
    m_obj.midi2vec()
    m_obj.vec2numpy()
    print(m_obj.midi_numpy)






