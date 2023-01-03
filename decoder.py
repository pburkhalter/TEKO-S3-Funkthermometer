import itertools
import time
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
        self.separate_by_timeout = 2000

        self.queue = queue
        self.db = db

        self.__running = True
        self.__signals = dict()
        self.__distance = 0
        self.__verify_group = None
        self.__group = 0
        self.__part = 0

        self.start()

    def start(self):
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
        normalized = self.normalize(item)
        filtered = self.filter(normalized)

        if filtered:
            group = self.__group
            part = self.__part
            timestamp = filtered[0]
            level = filtered[1]

            self.create(group, part)
            self.append(group, part, level)

        if self.__verify_group:
            verified = self.verify()

            for result in verified:
                self.out(verified[result])

        # self.save(group)

    def normalize(self, item):
        timestamp = item[0]
        level = item[1]

        if timestamp > (self.__distance + self.separate_by_timeout):
            self.__verify_group = self.__group
            self.__group += 1

        calculated_time = timestamp - self.__distance
        normalized_time = self.pulse_length[min(range(len(self.pulse_length)),
                                                key=lambda j: abs(self.pulse_length[j] - calculated_time))]

        self.__distance = timestamp

        return [normalized_time, level]

    def filter(self, normalized):
        timestamp = normalized[0]
        level = normalized[1]

        if timestamp >= 750:
            self.__part += 1
        elif timestamp >= 500:
            return [timestamp, level]
        else:
            return False

    def create(self, group, part):
        if group not in self.__signals:
            self.__signals[group] = dict()

        subdicts = {
            "timestamp": time.time(),
            "validated": False,
            "parts": dict()
        }

        for key in subdicts:
            if key not in self.__signals[group]:
                self.__signals[group][key] = subdicts[key]

        if part not in self.__signals[group]["parts"]:
            self.__signals[group]["parts"][part] = []

    def append(self, group, part, level):
        self.__signals[group]["parts"][part].append(level)

    def verify(self):
        results = dict()

        for group in self.__signals.copy():
            compared = []

            for part in self.__signals[group]["parts"].copy():
                # A valid signal consists of 36 bits. Delete parts that
                # don't have exactly 36 bits to filter out bad parts
                if len(self.__signals[group]["parts"][part]) != 36:
                    del self.__signals[group]["parts"][part]
                else:
                    compared.append(self.__signals[group]["parts"][part])

            # group lists by frequency to hopefully find the correct
            # signal, as we don't know how to compute the FCS (yet)
            verified = [list(i) for j, i in itertools.groupby(sorted(compared))]

            timestamp = self.__signals[group]["timestamp"]
            results[timestamp] = max(verified[0], key=len)

            # Delete group when we are done with it
            del self.__signals[group]

        self.__verify_group = None
        return results


    def save(self):
        # self.db
        pass

    def out(self, signal):

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

        if id2 == "00":
            station = "T2"
        else:
            station = "T1"

        if b == "1":
            battery = "OK"
        else:
            battery = "Low"

        temperature = BitArray(bin=temp1 + temp2 + temp3)
        temperature.invert()

        humidity = BitArray(bin=hum1 + hum2)
        humidity.invert()

        print("-" * 65)
        print("Temperature Recording: Station " + station + " @time (todo...)")
        print("-" * 65)

        print("Signal Encoded: " + id1 + " " + ch + " " + id2 + " " + v + " " + tr + " " + b + " " + temp1 + " " + temp2 + " " + temp3 + " " + hum1 + " " + hum2 + " " + fcs)

        print("Signal Decoded:")
        print("ID:\t\t\t" + str(BitArray(bin=id1).uint))
        print("Channel:\t\t" + str(BitArray(bin=ch).uint))
        print("Station:\t\t" + station)
        print("Battery:\t\t" + battery)
        print("Trend?:\t\t\t" + str(BitArray(bin=tr).uint))
        print("Button?:\t\t" + str(BitArray(bin=b).uint))
        print("Temperature:\t\t" + str((temperature.uint - 500) / 10) + "°C")
        print("Humidity:\t\t" + str(humidity.uint / 10) + "%")
        print("FCS:\t\t\t" + fcs)
