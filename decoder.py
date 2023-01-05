import time
import itertools
from datetime import datetime
from bitstring import BitArray
from pprint import pprint


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
        self.group = SignalGroup()

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
        # predefined timeout (offset). We assume we now have a
        # valid signal to save and will create a new group afterwards
        if timestamp > (self.__distance + self.part_timeout):
            if self.group.valid:
                print("Group valid...")
                #self.save(self.group) TODO
                self.out(self.group)
            else:
                print("Group not valid...")

            # create a new group (reset)
            self.group = SignalGroup()

        duration, level = self.normalize(timestamp, level)

        # indicating the end of the current part
        # and a possible beginning of a new part
        if duration >= 750:
            # this will be called multiple times, but we prevent
            # adding multiple empty parts in SignalGroup class
            self.group.add()

        # indicating a valid signal
        if duration == 500:
            self.group.append(level)

    def normalize(self, timestamp, level):
        calculated_duration = timestamp - self.__distance
        normalized_duration = self.pulse_length[min(range(len(self.pulse_length)),
                                                key=lambda j: abs(self.pulse_length[j] - calculated_duration))]

        self.__distance = timestamp
        return [normalized_duration, level]

    def save(self, group):
        self.db.add(
            group.id,
            group.station,
            group.timestamp,
            group.temperature,
            group.humidity,
        )

    def out(self, group):
        print("-" * 65)
        print("Temperature Recording: Station " + group.station + " @ " + group.datestring)
        print("-" * 65)
        print("Signal Encoded: " + group.bitstring)
        print("Signal Decoded:")
        print("ID1:\t\t\t" + group.id)
        print("ID2:\t\t\t" + group.id)
        print("Channel:\t\t" + group.channel)
        print("Battery:\t\t" + group.battery)
        print("Trend:\t\t\t" + group.trend)
        print("Station:\t\t" + group.station)
        print("Temperature:\t\t" + str(group.temperature) + "°C")
        print("Humidity:\t\t" + str(group.humidity) + "%")


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

        # computed attributes
        self.__bitstring = None
        self.__id = None
        self.__channel = None
        self.__battery = None
        self.__trend = None
        self.__station = None
        self.__temperature = None
        self.__humidity = None
        self.__datestring = None

        # add initial part
        self._parts.append(SignalPart())

    def add(self):
        # prevent adding a new part if the last part is empty
        if len(self._parts[len(self._parts) - 1]) != 0:
            part = SignalPart()
            self._parts.append(part)

    def append(self, level):
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
            self.compute(self._signal)

            self._validated = True
            return True
        return False

    def compute(self, signal):

        # get the corresponding bits
        _bitstring = "".join(map(str, signal))
        _id1 = "".join(map(str, signal[0:4]))
        _id2 = "".join(map(str, signal[4:6]))
        _channel = "".join(map(str, signal[6:8]))
        _battery = "".join(map(str, signal[8:9]))
        _trend = "".join(map(str, signal[9:11]))
        _station = "".join(map(str, signal[11:12]))
        _temperature = "".join(map(str, signal[12:24]))
        _humidity = "".join(map(str, signal[24:32]))
        _fcs = "".join(map(str, signal[32:36]))

        # calculate temperature
        temperature = BitArray(bin=_temperature)
        temperature.invert()
        temperature = (temperature.uint - 500) / 10

        # calculate humidity
        humidity = BitArray(bin=_humidity)
        humidity.invert()
        humidity = humidity.uint / 10

        # format datetime string
        datetime_ms = datetime.fromtimestamp(self._timestamp)
        datetime_str = datetime_ms.strftime("%m/%d/%Y, %H:%M:%S")

        if _station == "0":
            station = "T1"
        elif _station == "1":
            station = "T2"
        else:
            station = "Undefined"

        if _battery == "1":
            battery = "OK"
        elif _battery == "0":
            battery = "Low"
        else:
            battery = "Undefined"

        if _trend == "11":
            trend = "Rising"
        elif _trend == "10":
            trend = "Constant"
        elif _trend == "01":
            trend = "Falling"
        else:
            trend = "Undefined"

        self.__bitstring = _bitstring
        self.__temperature = temperature
        self.__humidity = humidity
        self.__id = _id1
        self.__channel = _channel
        self.__battery = battery
        self.__trend = trend
        self.__station = station
        self.__datestring = datetime_str

    def __len__(self):
        return len(self._parts)

    @property
    def valid(self):
        return self.validate()

    @property
    def timestamp(self):
        return self._timestamp

    @property
    def bitstring(self):
        return self.__bitstring

    @property
    def id(self):
        return self.__id

    @property
    def channel(self):
        return self.__channel

    @property
    def battery(self):
        return self.__battery

    @property
    def trend(self):
        return self.__trend

    @property
    def station(self):
        return self.__station

    @property
    def temperature(self):
        return self.__temperature

    @property
    def humidity(self):
        return self.__humidity

    @property
    def datestring(self):
        return self.__datestring

