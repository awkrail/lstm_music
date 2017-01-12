# coding: utf-8
import binascii
import sys
import numpy as np
sys.setrecursionlimit(1000000)

class vec2binary():
    def __init__(self, header, truck, midi_numpy, time):
        self.header = header
        self.truck = truck
        # TODO: トラックチャネルのデータ部分のデータ長は後々midiを作成してから変更可能にする。
        self.midi_numpy = midi_numpy
        self.midi_ary = []
        self.T = time
        self.detailed_ary = [[0 for _ in range(128)] for _ in range(self.T)]
        self.boolean = [[False for _ in range(128)] for _ in range(self.T)]
        self.dict_ary = []
        self.tmp_ary = []

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
        truck_type = [byt for byt in self.truck['truck_chunk']]
        data_length = ['00', '00', '00', '00']
        truck_data = [truck_type, data_length]
        for truck_ary in truck_data:
            for byt in truck_ary:
                self.midi_ary.append(byt)

    def numpy2ary(self):
        time_unit = eval('0x' + self.header['time_unit'][0] + self.header['time_unit'][1])
        sixteenth = int(time_unit / 4)

        for vec_index, vec in enumerate(self.midi_numpy):
            for index, elem in enumerate(vec):
                if elem > 0:
                    start = vec_index*sixteenth
                    end = start + sixteenth
                    for i in range(start, end):
                        if i < self.T:
                            self.detailed_ary[i][index] = int(elem)
                        else:
                            break

    def ary2dict(self):
        for vec_index, vec in enumerate(self.detailed_ary):
            for index, elem in enumerate(vec):
                if elem > 0 and self.boolean[vec_index][index] is False:
                    start = vec_index
                    end = start
                    for i in range(start, len(self.detailed_ary)):
                        if self.detailed_ary[i][index] > 0:
                            end += 1
                            self.boolean[i][index] = True
                        else:
                            break
                    velocity = hex(elem)
                    note = hex(index)
                    tmp_dict_start = {'order_time': start, 'channel': '90', 'velocity': velocity[2:],
                                      'note': note[2:]}
                    tmp_dict_end = {'order_time': end, 'channel': '90', 'velocity': '00', 'note': note[2:]}
                    self.dict_ary.append(tmp_dict_start)
                    self.dict_ary.append(tmp_dict_end)

        self.dict_ary.sort(key=lambda x:x['order_time'])
        # order_timeの順番にデータをソートする。

    def dict_ary2midi(self):
        tmp_ary = []
        time_unit = eval('0x' + self.header['time_unit'][0] + self.header['time_unit'][1])
        sixteenth = hex(int(time_unit / 4))

        # 最初の要素だけは別で入れておく。
        tmp_ary.append(self.dict_ary[0]['channel'])
        tmp_ary.append(self.dict_ary[0]['note'])
        tmp_ary.append(self.dict_ary[0]['velocity'])
        del self.dict_ary[0]

        for i, dict in enumerate(self.dict_ary):
            # print(i)
            delta_time = dict['order_time'] - self.dict_ary[i-1]['order_time']
            print(delta_time)

            # 一回目だけの処理
            if i == 0:
                tmp_ary.append('00')
                self.append2ary(tmp_ary, dict)
                continue
            # delta_timeがないとき
            if delta_time == 0:
                tmp_ary.append('00')
                self.append2ary(tmp_ary, dict)
            else:
                # delta_timeがあるとき。
                # delta_timeが0x80(128)を超える長さの時,可変長数値表現にする処理が必要
                if delta_time >= eval('0x80'):
                    delta_times = convert(delta_time)
                    print(delta_times)
                    # TODO:ここではさらに,delta_timeが可変長数値表現以上の時を考える必要あり。
                    for delta_time in delta_times:
                        tmp_ary.append(delta_time[2:])
                    self.append2ary(tmp_ary, dict)
                else:
                    tmp = hex(delta_time)
                    tmp_ary.append(tmp[2:])
                    self.append2ary(tmp_ary, dict)

        self.tmp_ary = tmp_ary

    def append2ary(self,ary,dict):
        ary.append(dict['channel'])
        ary.append(dict['note'])
        ary.append(dict['velocity'])


def convert(val):
    buffer = []
    buffer.append((0x7f & val))
    val = (val >> 7)
    while val > 0:
        buffer.append(0x80 + (val & 0x7f))
        val = (val >> 7)
    buffer.sort(reverse=True)
    print(buffer)
    buffer = ary2hex(buffer)

    return buffer


def ary2hex(ary):
    return_ary = []
    for elm in ary:
        if elm == 0:
            dt = '0x00'
            return_ary.append(dt)
        else:
            dt = hex(elm)
            return_ary.append(dt)

            # TODO:三項演算子でそれぞれを16進数にしていく
    return return_ary









