import itertools
import time
from datetime import datetime
from pprint import pprint

from bitstring import BitArray
import sqlite3 as sqlite


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

    def __init__(self, queue, db):
        self.pulse_length = [0, 250, 500, 750, 1000]
        self.part_timeout = 2000

        self.queue = queue
        self.db = db

        # create initial group
        self.__group = SignalGroup()

        self.__running = False
        self.__distance = 0
        self.__timestamp = 0

        self.start()

    def start(self):

        # db connection
        self.db.connect()
        self.db.setup()

        # loop
        self.__running = True
        while self.__running:
            if not self.queue.empty():
                item = self.queue.get()
                self.decode(item)
            else:
                time.sleep(1)

    def stop(self):
        self.__running = False

    def decode(self, item):
        timestamp, level = item

        # check if distance to previous group is bigger than
        # predefined timeout (offset) and create new group (and part)
        if timestamp > (self.__distance + self.part_timeout):
            self.__group.validate()
            self.save()
            self.__group = SignalGroup()

        duration, level = self.normalize(timestamp, level)

        # indicating the end of the current part
        # and a possible beginning of new part
        if duration >= 750:
            # this will be called multiple times, but we
            # prevent adding multiple empty parts in SignalGroup
            self.__group.add()

        # indicating a valid signal
        if duration == 500:
            self.__group.extend_last_part(level)

        self.save()

    def normalize(self, timestamp, level):
        calculated_duration = timestamp - self.__distance
        normalized_duration = self.pulse_length[min(range(len(self.pulse_length)),
                                                key=lambda j: abs(self.pulse_length[j] - calculated_duration))]

        self.__distance = timestamp

        return [normalized_duration, level]

    def save(self):
        # self.db.add( ........ )
        self.out(self.__group)

    def out(self, signal_object):

        signal = signal_object.signal

        if not signal:
            return False

        id1 = "".join(map(str, signal[0:4]))
        id2 = "".join(map(str, signal[4:6]))
        ch = "".join(map(str, signal[6:8]))
        v = "".join(map(str, signal[8:9]))
        tr = "".join(map(str, signal[9:11]))
        st = "".join(map(str, signal[11:12]))
        temp1 = "".join(map(str, signal[12:16]))
        temp2 = "".join(map(str, signal[16:20]))
        temp3 = "".join(map(str, signal[20:24]))
        hum1 = "".join(map(str, signal[24:28]))
        hum2 = "".join(map(str, signal[28:32]))
        fcs = "".join(map(str, signal[32:36]))

        if st == "1":
            station = "T2"
        elif st == "0":
            station = "T1"
        else:
            station = "Undefined"

        if v == "1":
            battery = "OK"
        elif v == "0":
            battery = "Low"
        else:
            battery = "Undefined"

        if tr == "11":
            trend = "Rising"
        elif tr == "10":
            trend = "Constant"
        elif tr == "01":
            trend = "Falling"
        else:
            trend = "Undefined"

        temperature = BitArray(bin=temp1 + temp2 + temp3)
        temperature.invert()

        humidity = BitArray(bin=hum1 + hum2)
        humidity.invert()

        #Date
        dto = datetime.fromtimestamp(signal_object.timestamp)
        dts = dto.strftime("%m/%d/%Y, %H:%M:%S")

        print("-" * 65)
        print("Temperature Recording: Station " + station + " @ " + dts)
        print("-" * 65)

        print("Signal Encoded: " + id1 + " " + st + " " + ch + " " + v + " " + tr + " " + id2 + " " + temp1 + " " + temp2 + " " + temp3 + " " + hum1 + " " + hum2 + " " + fcs)

        print("Signal Decoded:")
        print("ID1:\t\t\t" + str(BitArray(bin=id1).uint))
        print("ID2:\t\t\t" + str(BitArray(bin=id2).uint))
        print("Channel:\t\t" + str(BitArray(bin=ch).uint))
        print("Battery:\t\t" + battery)
        print("Trend:\t\t\t" + trend)
        print("Station:\t\t" + station)
        print("Temperature:\t\t" + str((temperature.uint - 500) / 10) + "°C")
        print("Humidity:\t\t" + str(humidity.uint / 10) + "%")
        print("FCS:\t\t\t" + fcs)


class SignalPart:
    def __init__(self):
        self._bits = []
        self._validated = False

    def append(self, bit: int):
        self._bits.append(bit)

    def delete(self, position: int):
        del self._bits[position]

    def validate(self):
        # A valid signal consists of 36 bits. Return false if
        # we don't have exactly 36 bits to filter them out
        if len(self._bits) == 36:
            self._validated = True
        else:
            self._validated = False

        return self._validated

    @property
    def valid(self):
        return self.validate()

    def __len__(self):
        return len(self._bits)


class SignalGroup:
    def __init__(self):
        self._signal = []
        self._parts = []

        self._validated = False
        self._timestamp = datetime.now().timestamp()

        # add initial part
        self._parts.append(SignalPart())

    def add(self):
        # prevent adding a new part if the last part is empty
        if len(self._parts[len(self._parts) - 1]) != 0:
            part = SignalPart()
            self._parts.append(part)

    def append(self, part: SignalPart):
        self._parts.append(part)

    def extend_last_part(self, level):
        self._parts[len(self._parts) - 1].append(level)

    def delete(self, position: int):
        del self._parts[position]

    def validate(self):
        parts_list = []
        for i, part in enumerate(self._parts):
            # A valid signal consists of 36 bits. Delete parts that
            # don't have exactly 36 bits to filter them out
            if part.valid:
                parts_list.append(part._bits)

        # group lists by frequency to hopefully find the correct
        # signal, as we don't know how to compute the FCS (yet)
        verified = [list(i) for j, i in itertools.groupby(sorted(parts_list))]

        if verified:
            self._signal = max(verified[0], key=len)
            self._validated = True

        return self._signal

    @property
    def valid(self):
        return self.validate()

    @property
    def timestamp(self):
        return self._timestamp

    @property
    def parts(self):
        return self._parts

    @property
    def signal(self):
        return self._signal

    @property
    def last_part(self):
        return self._parts[len(self._parts) - 1]

    def __len__(self):
        return len(self._parts)

