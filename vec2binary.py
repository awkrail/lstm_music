# coding: utf-8
import binascii
import sys
import numpy as np
sys.setrecursionlimit(1000000)

class vec2binary():
    def __init__(self, header, truck, midi_numpy):
        self.header = header
        self.truck = truck
        # TODO: トラックチャネルのデータ部分のデータ長は後々midiを作成してから変更可能にする。
        self.midi_numpy = midi_numpy
        self.midi_ary = []

    def set_header(self):
        chunck_type = [byt for byt in self.header['chunk_type']]
        header_size = [byt for byt in self.header['header_size']]
        format = [byt for byt in self.header['format']]
        track = [byt for byt in self.header['track']]
        time_unit = [byt for byt in self.header['time_unit']]
        header_data = [chunck_type, header_size, format, track, time_unit]
        for header_ary in header_data:
            for byt in header_ary:
                self.midi_ary.append(byt)

    def set_truck(self):
        truck_type = [byt for byt in self.truck['track_chunk']]
        data_length = ['00', '00', '00', '00']
        truck_data = [truck_type, data_length]
        for truck_ary in truck_data:
            for byt in truck_ary:
                self.midi_ary.append(byt)


    def numpy2ary(self):
        pass

