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

    def __init__(self,midi_ary):
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
        #print(delta_time)
        #print(event_data)
        self.result.append({
            'delta_time': delta_time,
            'event_data': event_data
        })
        #print(self.result)
        if len(self.data_ary) > 0:
            self.parse_data()

    def take_true_data(self):
        track = []
        for rlt in self.result:
            if rlt["event_data"]["bool"] == True:
                track.append(rlt)
        print("Done!")
        self.result = track

    def delta_to_time_order(self):
        t_n = 0
        result_ary = []
        for rlt in self.result:
            delta = rlt["delta_time"]
            t_n = t_n + delta
            result_ary.append({
                'order_time' : t_n + 1,
                'event_data' : rlt['event_data']
            })

        fixed_order_ary = []

        for rlt in result_ary:
            if eval(rlt['event_data']['velocity']) == 0:
                rlt['order_time'] -= 1
                fixed_order_ary.append(rlt)
            else:
                fixed_order_ary.append(rlt)

        return fixed_order_ary


    def get_deltatime(self):
        i = 0
        tmp_bit = 0
        while eval('0x' + self.data_ary[i]) >= 0x80:
            a = eval('0x' + self.data_ary[i]) ^ (1 << 7)
            tmp_bit = (a << 7)
            i += 1
        delta_bit = tmp_bit | eval('0x' + self.data_ary[i])
        #print(self.data_ary[i])
        #print(delta_bit)
        self.data_ary = self.data_ary[i+1:]
        return delta_bit

    def get_event(self):
        data = {}
        status_byte = self.data_ary[0]
        bin2int = eval('0x' + status_byte)
        if bin2int == 0xFF:
            size = eval('0x' + self.data_ary[2])
            self.data_ary = self.data_ary[3+size:]

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
                self.data_ary = self.data_ary[i+2:]

            if bin2int == 0xF1 or bin2int == 0xF3:
                self.data_ary = self.data_ary[2:]

            if bin2int == 0xF2:
                self.data_ary = self.data_ary[3:]

        if len(data) == 0:
            data["bool"] = False

        return data

class midi2vec():
    """
    分解能/4ずつ(16分音符ずつ),音がなっているかどうかをチェックし,
    鳴っている音を特定,1/96分で1要素となる配列を生成し,それを24ずつ区切りでスライスしベクトル化するクラス。
    """
    def __init__(self, track_ary, time_unit):
        self.track = track_ary
        self.time_unit = eval('0x' + time_unit[0] + time_unit[1])
        self.T = track_ary[-1]["order_time"]
        self.midiAry = []
        self.result = []

    def roop_del(self):
        status = 0
        cdary_num = 0
        order_time_ary = [dit['order_time'] for dit in self.track]

        for i in range(self.T):
            # こちらは連続的な時間としてとる。
            if i in order_time_ary:
                # ここのif文は,track_aryの全配列の要素のorder_timeの中にあるかどうか。離散値なので連続的にチェックする。
                command_ary = [command for command in self.track if command["order_time"] == i]
                print(command_ary)
                # ここまではうまくとれているようである。
                for command in command_ary:
                    if eval('0x' + command['event_data']['velocity']) > 0:
                        status = 1
                        self.midi2ary(command)
                        # print(self.midiAry)
                        cdary_num += 1
                        if cdary_num == len(command_ary) - 1:
                            # TODO:ここの分岐が怪しい気がする。水曜日にがっつりデバッグする。
                            self.join_ary(cdary_num)
                    else:
                        status = 0
            else:
                if status == 1:
                    self.recursive_midi2ary(status)
                else:
                    self.recursive_midi2ary(status)

    def midi2ary(self, command):
        piano_vec = [0 for _ in range(128)]
        sound = eval('0x' + command['event_data']["note"])
        piano_vec[sound] = 1
        self.midiAry.append(piano_vec)

    def join_ary(self, ary_length):
        lists = [self.midiAry[-i] for i in range(1, ary_length+1)]
        others = 10 - ary_length
        # 配列の数が可変であり,そのままだと計算ができないので10個に合わせる。
        other_lists = [[0 for _ in range(128)] for _ in range(others)]
        lists.extend(other_lists)
        l1, l2, l3, l4, l5, l6, l7, l8, l9, l10 = lists[0], lists[1], lists[2], lists[3], lists[4], \
                                         lists[5], lists[6], lists[7], lists[8], lists[9]

        combined_list = [a + b + c + d + e + f + g + h + i + j for a, b, c, d, e, f, g, h, i, j in zip(l1, l2, l3,
                                                                                                       l4, l5, l6, l7,
                                                                                                       l8, l9, l10)]
        self.result.append(combined_list)
        # TODO:listsの値から,要素ごとに足し算した値を作成し,self.midiAryから結合した部分を取り出して作った方を追加する。
        # TODO:もしくは,新しく配列オブジェクトを作るかをする。


    def recursive_midi2ary(self,status):
        if status == 1:
            same_list = self.result[-1].copy()
            self.result.append(same_list)
        else:
            zero_list = [0 for _ in range(128)]
            self.result.append(zero_list)


    def midi2numpy(self):
        pass

with open("practice_midi/UN.mid", 'rb') as f:
    str = f.read()
    hexlify = binascii.hexlify(str)

midi_ary = [hexlify[i:i+2].decode('utf-8').upper() for i in range(0, len(hexlify), 2)]
#print(midi_ary)

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
#print(midi.result)
print("--------------------")
midi.take_true_data()
track = midi.delta_to_time_order()

to_vec_obj = midi2vec(track,midi.header["time_unit"])
to_vec_obj.roop_del()

#print(to_vec_obj.result)