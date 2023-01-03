import logging

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

# Recent sample
# 1001  01  00  0  10  1  1101 0011 1111  1101 1010  0011


class Decoder:

    def __init__(self, file=None):
        self.timedelta = [0, 250, 500, 750, 1000]
        self.level_low = "1000C1FF"
        self.level_high = "1080C1FF"

        self.raw_content = None
        self.raw_parts = []

        self.parts = []
        self.chunks = []
        self.signal = []

        if file:
            self.decode(file)

    def read_from_file(self, file):
        try:
            with open(file) as f_obj:
                lines = f_obj.readlines()
        except FileNotFoundError:
            logging.error("Sorry, the file " + file + " does not exist.")
        except IsADirectoryError:
            logging.error("Sorry, the file " + file + " is a directory.")
        except PermissionError:
            logging.error("Sorry, the file " + file + " cant be accessed because of a permission error.")
        except IOError:
            logging.error("Sorry, the file " + file + " cant be opened because of an IOError.")

        self.raw_content = lines

    def extract(self):
        offset = None

        for line in self.raw_content:
            # Skipping comments
            if not line.startswith('#'):
                # get initial time offset
                if offset is None:
                    offset = line.split()[0]

                # strip newline character
                stripped_line = line.strip()

                # left: time / right: level
                time, level = stripped_line.split()
                self.raw_parts.append([int(time) - int(offset), level])

    def normalize(self):
        items = self.raw_parts
        for i, item in enumerate(items):
            time = item[0]
            level = item[1]

            distance = 0
            if i > 0: distance = int(items[i - 1][0])

            calculated_time = time - distance
            normalized_time = self.timedelta[min(range(len(self.timedelta)),
                                                 key=lambda j: abs(self.timedelta[j]-calculated_time))]

            if level == self.level_low:
                normalized_level = 0
            elif level == self.level_high:
                normalized_level = 1
            else:
                raise EncodingWarning('The provided level seems to be malformed!')

            self.parts.append([normalized_time, normalized_level])

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

    def decode(self, file):
        self.read_from_file(file)
        self.extract()
        self.normalize()
        self.split()
        self.filter()

        return self.signal
