# coding: utf-8
import binascii
import sys
import numpy as np
sys.setrecursionlimit(1000000)


class MidiParser():
    """
    バイナリデータのmidiファイルを
    header部分,チャンク部分に切り分け,
    note-on,note-offのデータのみを取り出すクラス。

    TODO:エクスクルーシブメッセージ(F0~F7)のものがあるmidiデータへの対応,複数トラックへの対応は未処理。
    """

    def __init__(self, midi_ary):
        self.midi_ary = midi_ary
        self.truck_ary = []
        self.data_ary = []
        self.header = {}
        self.truck = {}
        self.meta = {}
        self.result = []

    def parse_head(self):
        if self.midi_ary[0] == "4D" and self.midi_ary[1] == "54" and \
                        self.midi_ary[2] == "68" and self.midi_ary[3] == "64":
            self.header = {
                'chunk_type': self.midi_ary[0:4],
                'header_size': self.midi_ary[4:8],
                'format': self.midi_ary[8:10],
                'track': self.midi_ary[10:12],
                'time_unit': self.midi_ary[12:14]
            }
            self.truck_ary = self.midi_ary[14:]
        else:
            print('形式エラーです')

    def parse_truck(self):
        if self.truck_ary[0] == "4D" and self.truck_ary[1] == "54" \
                and self.truck_ary[2] == "72" and self.truck_ary[3] == "6B":
            self.truck = {
                'truck_chunk': self.truck_ary[0:4],
                'data_length': self.truck_ary[4:8],
            }
            self.data_ary = self.truck_ary[8:]

    def parse_data(self):
        delta_time = self.get_deltatime()
        event_data = self.get_event()
        # print(delta_time)
        # print(event_data)
        self.result.append({
            'delta_time': delta_time,
            'event_data': event_data
        })
        # print(self.result)
        if len(self.data_ary) > 0:
            self.parse_data()

    def take_true_data(self):
        track = []
        for rlt in self.result:
            if rlt["event_data"]["bool"] == True:
                track.append(rlt)
        self.result = track

    def delta_to_time_order(self):
        t_n = 0
        result_ary = []
        for rlt in self.result:
            delta = rlt["delta_time"]
            t_n = t_n + delta
            result_ary.append({
                'order_time': t_n,
                'event_data': rlt['event_data']
            })

        fixed_order_ary = []


        for rlt in result_ary:
            if eval('0x' + rlt['event_data']['velocity']) == 0:
                rlt['order_time'] -= 1
                fixed_order_ary.append(rlt)
            else:
                fixed_order_ary.append(rlt)

        #print("Done!")
        return fixed_order_ary

    def get_deltatime(self):
        i = 0
        tmp_bit = 0
        while eval('0x' + self.data_ary[i]) >= 0x80:
            a = eval('0x' + self.data_ary[i]) ^ (1 << 7)
            tmp_bit = (a << 7)
            i += 1
        delta_bit = tmp_bit | eval('0x' + self.data_ary[i])
        # print(self.data_ary[i])
        # print(delta_bit)
        self.data_ary = self.data_ary[i + 1:]
        return delta_bit

    def get_event(self):
        data = {}
        status_byte = self.data_ary[0]
        bin2int = eval('0x' + status_byte)
        if bin2int == 0xFF:
            size = eval('0x' + self.data_ary[2])
            self.data_ary = self.data_ary[3 + size:]

        elif 0x80 <= bin2int <= 0x9F:
            data["bool"] = True
            data["channel"] = self.data_ary[0]
            data["note"] = self.data_ary[1]
            data["velocity"] = self.data_ary[2]
            self.data_ary = self.data_ary[3:]

        elif 0x9F < bin2int:
            if 0xA0 <= bin2int <= 0xAF:
                self.data_ary = self.data_ary[3:]

            if 0xB0 <= bin2int <= 0xBF:
                if self.data_ary[1] == 0x00 and self.data_ary[4] == 0x20:
                    self.data_ary = self.data_ary[6:]
                else:
                    self.data_ary = self.data_ary[3:]

            if 0xC0 <= bin2int <= 0xDF:
                self.data_ary = self.data_ary[2:]

            if 0xE0 <= bin2int <= 0xEF:
                self.data_ary = self.data_ary[3:]

            if bin2int == 0xF0:
                i = 0
                while eval(self.data_ary[i]) != 0xF7:
                    i += 1
                self.data_ary = self.data_ary[i + 2:]

            if bin2int == 0xF1 or bin2int == 0xF3:
                self.data_ary = self.data_ary[2:]

            if bin2int == 0xF2:
                self.data_ary = self.data_ary[3:]

        if len(data) == 0:
            data["bool"] = False

        return data


class Mid2vec():
    """
    分解能/4ずつ(16分音符ずつ),音がなっているかどうかをチェックし,
    鳴っている音を特定,1/96分で1要素となる配列を生成し,それを24ずつ区切りでスライスしベクトル化するクラス。
    """
    def __init__(self, track_ary, time_unit):
        self.track = track_ary
        self.time_unit = eval('0x' + time_unit[0] + time_unit[1])
        self.T = track_ary[-1]['order_time']
        self.midi_ary = [[0 for _ in range(128)] for _ in range(self.T)]
        self.midi_numpy = []

    def midi2vec(self):
        for on_command in self.track:
            if eval('0x' + on_command['event_data']['velocity']) > 0:
                for off_command in self.track:
                    if on_command['event_data']['note'] == off_command['event_data']['note'] and \
                            eval('0x' + off_command['event_data']['velocity']) == 0 and \
                            off_command['order_time'] > on_command['order_time']:

                        start_time = on_command['order_time']
                        end_time = off_command['order_time']
                        note = eval('0x' + on_command['event_data']['note'])
                        velocity = eval('0x' + on_command['event_data']['velocity'])
                        self.draw1ary(start_time, end_time, note, velocity)
                        break
                    else:
                        continue

    def draw1ary(self, start_time, end_time, note, velocity):
        for i in range(start_time, end_time + 1):
            if i < self.T:
                self.midi_ary[i][note] = velocity
            else:
                break

    def vec2numpy(self):
        sixteenth_note = int(self.time_unit / 4)
        tmp_ary = [self.midi_ary[i:i + sixteenth_note] for i in range(0, self.T, sixteenth_note)]
        for ary_per_sixteenth in tmp_ary:
            note_ary = []
            for vector in ary_per_sixteenth:
                for index, velocity in enumerate(vector):
                    if velocity > 0:
                        note_ary.append((index, velocity))
                    else:
                        continue

            set_ary = sorted(set(note_ary), key=note_ary.index)
            #print(set_ary)
            vec_nt = [0 for _ in range(128)]
            for index, velocity in set_ary:
                vec_nt[index] = velocity
            self.midi_numpy.append(vec_nt)

        self.midi_numpy = np.array(self.midi_numpy, dtype=np.float32)