from bitstring import BitArray

# ID1  ->    ID 1
# CH   ->    Channel
# ID2  ->    ID 2
# V    ->    Voltage (Battery ok/nok)
# TR   ->    Temperature Trend (00 – stable, 01 – increasing, 10 – decreasing)
# B    ->    Battery changed
# TEMP ->    Temperature (500 -> 00.000 Degree)
# HUM  ->    Humidity
# FCS  ->    Frame Check Sequence (only for Humidity?)

# ID1   CH  ID2 V  TR  B  TEMP            HUM        FCS
# 0010  00  11  0  01  0  0001 1111 0100  1001 1111  1110   / -00 Grad (T2)  500 -> 00.000 Degree


class SignalDecoder:

    def __init__(self, file=None):
        self.pulse_length = [0, 250, 500, 750, 1000]
        self.level_low = 0
        self.level_high = 1

        self.raw = []
        self.parts = []
        self.chunks = []

        self.signal = []

    def append(self, timecode, level):
        self.raw.append([timecode, level])

    def normalize(self):
        items = self.raw
        for i, item in enumerate(items):
            time = item[0]
            level = item[1]

            distance = 0
            if i > 0: distance = int(items[i - 1][0])

            calculated_time = time - distance
            normalized_time = self.pulse_length[min(range(len(self.pulse_length)),
                                                    key=lambda j: abs(self.pulse_length[j] - calculated_time))]

            self.parts.append([normalized_time, level])

    def split(self):
        split_part = []

        for part in self.parts:
            time = part[0]

            if time < 750:
                split_part.append(part)
            else:
                self.chunks.append(split_part)
                split_part.clear()

    def filter(self):
        for chunk in self.chunks:
            signal = []
            for part in chunk:
                time = part[0]
                level = part[1]

                if time >= 500:
                    signal.append(level)
            self.signal.append(signal)

    def verify(self):
        # A valid signal consists of 36 bits
        for i, signal in enumerate(self.signal):
            if len(signal) != 36:
                del self.signal[i]

    def decode(self):
        self.normalize()
        self.split()
        self.filter()
        self.verify()

    def out(self):

        for signal in self.signal:
            if len(signal) != 36:
                break

            id1 = "".join(map(str, signal[0:4]))
            ch = "".join(map(str, signal[4:6]))
            id2 = "".join(map(str, signal[6:8]))
            v = "".join(map(str, signal[8:9]))
            tr = "".join(map(str, signal[9:11]))
            b = "".join(map(str, signal[11:12]))
            temp1 = "".join(map(str, signal[12:16]))
            temp2 = "".join(map(str, signal[16:20]))
            temp3 = "".join(map(str, signal[20:24]))
            hum1 = "".join(map(str, signal[24:28]))
            hum2 = "".join(map(str, signal[28:32]))
            fcs = "".join(map(str, signal[32:36]))

            print("Signal Encoded: " + id1 + " " + ch + " " + id2 + " " + v + " " + tr + " " + b + " " + temp1 + " " + temp2 + " " + temp3 + " " + hum1 + " " + hum2 + " " + fcs)
            print("Signal Decoded:")

            print("ID:\t\t\t" + str(BitArray(bin=id1).uint))
            print("Channel:\t\t" + str(BitArray(bin=ch).uint))

            if id2 == "00":
                station = "T2"
            else:
                station = "T1"
            print("Station:\t\t" + station)

            if b == "1":
                battery = "OK"
            else:
                battery = "Low"
            print("Battery:\t\t" + battery)

            print("Trend?:\t\t\t" + str(BitArray(bin=tr).uint))
            print("Button?:\t\t" + str(BitArray(bin=b).uint))

            temperature = BitArray(bin=temp1 + temp2 + temp3)
            temperature.invert()
            print("Temperature:\t\t" + str((temperature.uint - 500) / 10) + "°C")

            humidity = BitArray(bin=hum1 + hum2)
            humidity.invert()
            print("Humidity:\t\t" + str(humidity.uint) + "%")

            print("FCS:\t\t\t" + fcs)
            print("-" * 60)
