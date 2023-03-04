import time
import itertools
from datetime import datetime
from bitstring import BitArray


# ID1  ->    ID 1
# CH   ->    Channel
# ID2  ->    ID 2
# V    ->    Voltage (Battery ok/nok)
# TR   ->    Temperature Trend (00 – stable, 01 – increasing, 10 – decreasing)
# B    ->    Battery changed
# TEMP ->    Temperature (500 -> 00.000 Degree)
# HUM  ->    Humidity
# FCS  ->    Frame Check Sequence (XOR separate for temp and hum?)

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
        self.db.drop()
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
        self.__running = Falseva

    def decode(self, item):
        timestamp, level = item

        # check if distance to previous group is bigger than
        # predefined timeout (offset). We assume we now have a
        # valid signal to save and will create a new group afterwards
        if timestamp > (self.__distance + self.part_timeout):
            if self.group.valid:
                self.save(self.group)
                self.out(self.group)

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
        self.db.add_measurement(
            group.station,
            group.datestring,
            group.temperature,
            group.humidity,
            group.bitstring
        )

    def out(self, group):
        print("-" * 80)
        print("Temperature Recording: Station " + group.station + " @ " + group.datestring)
        print("-" * 80)
        print("Signal Descrip: " + "Ch   00 ID ?? B  Temperature    Humidity  00 ??")
        print("Signal Encoded: " + group.bitstring_nice)
        print(" ")
        print("Signal Decoded:")
        print("Channel:\t\t" + str(group.channel))
        print("Station:\t\t" + group.station)
        print("Battery:\t\t" + group.battery)
        print("Temperature:\t\t" + str(group.temperature) + "°C")
        print("Humidity:\t\t" + str(group.humidity) + "%")
        print("-" * 80)


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
        self.__bitstring_nice = None
        self.__channel = None
        self.__battery = None
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
        _bitparts = [
            _bitstring[0:4],
            _bitstring[4:6],
            _bitstring[6:8],
            _bitstring[8:10],
            _bitstring[10:12],
            _bitstring[12:16],
            _bitstring[16:20],
            _bitstring[20:24],
            _bitstring[24:28],
            _bitstring[28:32],
            _bitstring[32:34],
            _bitstring[34:36]
        ]

        # Bitstring with visual separation
        bitstring_separated = " ".join(_bitparts)

        # Station
        station = _bitstring[6:8]
        if station == "00":
            station = "T1"
        elif station == "01":
            station = "T2"
        else:
            station = "Undefined"

        # Battery
        battery = _bitstring[10:12]
        if battery == "10":
            battery = "OK"
        elif battery == "01":
            battery = "Low"
        else:
            battery = "Undefined"

        # Channel
        channel = BitArray(bin=_bitstring[0:4])
        channel = channel.uint

        # Temperature
        temperature = BitArray(bin=_bitstring[13:24])
        temperature.invert()
        temperature = (temperature.uint - 500) / 10

        # Humidity
        humidity = BitArray(bin=_bitstring[25:32])
        humidity.invert()
        humidity = (humidity.uint / 2)

        # Datetime string
        datetime_ms = datetime.fromtimestamp(self._timestamp)
        datetime_str = datetime_ms.strftime("%d/%m/%Y, %H:%M:%S")

        self.__bitstring = _bitstring
        self.__bitstring_nice = bitstring_separated
        self.__temperature = temperature
        self.__humidity = humidity
        self.__channel = channel
        self.__battery = battery
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
    def bitstring_nice(self):
        return self.__bitstring_nice

    @property
    def channel(self):
        return self.__channel

    @property
    def battery(self):
        return self.__battery

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
