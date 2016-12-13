import binascii

with open("practice_midi/UN.mid",'rb') as f:
    str = f.read()
    hexlify = binascii.hexlify(str)

midi_ary = [hexlify[i:i+2].decode('utf-8') for i in range(0, len(hexlify), 2)]

class MidiParser():
    def __init__(self,midi_ary):
        self.midi_ary = midi_ary
        self.truck_ary = []
        self.data_ary = []
        self.header = {}
        self.truck = {}

    def parse_head(self):
        if self.midi_ary[0] == "4d" and self.midi_ary[1] == "54" and \
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
            print('形式エラーです。')

    def parse_truck(self):
        if self.truck_ary[0] == "4d" and self.truck_ary[1] == "54" \
                and self.truck_ary[2] == "72" and self.truck_ary[3] == "6b":
            self.truck = {
                'truck_chunk': self.truck_ary[0:4],
                'data_length': self.truck_ary[4:8],
            }
            self.data_ary = self.truck_ary[8:]

    def meta_data(self):
        if self.data_ary[0] == "FF":
            


midi = MidiParser(midi_ary)
midi.parse_head()
midi.parse_truck()
print("-------header-------")
print(midi.header)
print("-------chunk--------")
print(midi.truck)
print("--------------------")
