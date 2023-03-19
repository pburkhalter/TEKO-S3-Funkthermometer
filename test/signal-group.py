import unittest
from datetime import datetime
from decoder import SignalGroup


class SignalGroupTestCase(unittest.TestCase):
    def setUp(self):
        self.group = SignalGroup()
        self.group.append(0)
        self.group.append(0)
        self.group.append(1)
        self.group.append(0)
        self.group.append(0)
        self.group.append(1)
        self.group.append(1)
        self.group.append(1)
        self.group.append(0)
        self.group.append(0)
        self.group.append(0)
        self.group.append(1)
        self.group.append(1)
        self.group.append(1)
        self.group.append(1)
        self.group.append(0)
        self.group.append(1)
        self.group.append(1)
        self.group.append(1)
        self.group.append(1)
        self.group.append(1)
        self.group.append(0)
        self.group.append(1)
        self.group.append(1)
        self.group.append(1)
        self.group.append(1)
        self.group.append(1)
        self.group.append(1)
        self.group.append(1)
        self.group.append(0)
        self.group.append(0)
        self.group.append(0)
        self.group.append(0)
        self.group.append(0)
        self.group.append(0)
        self.group.append(1)
        self.group.append(0)
        self.group.append(0)
        self.group.append(0)
        self.group.append(1)

    def tearDown(self):
        self.group = None

    def test_append(self):
        self.group.append(1)
        self.assertEqual(self.group.bits, [0, 0, 1, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1])

    def test_add(self):
        self.group.add()
        self.assertEqual(len(self.group.parts), 2)
        self.group.add()
        self.assertEqual(len(self.group.parts), 2)

    def test_validate(self):
        self.assertTrue(self.group.validate())

    def test_station(self):
        self.assertEqual(self.group.station, "0010")

    def test_channel(self):
        self.assertEqual(self.group.channel, "00")

    def test_id(self):
        self.assertEqual(self.group.id, "11")

    def test_voltage(self):
        self.assertEqual(self.group.battery, "0")

    def test_temperature(self):
        self.assertEqual(self.group.temperature, 0)

    def test_humidity(self):
        self.assertEqual(self.group.humidity, 48)

    def test_bitstring(self):
        self.assertEqual(self.group.bitstring, "001000110010000011110100100111111110")

    def test_datestring(self):
        self.assertEqual(self.group.datestring, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    def test_valid(self):
        self.assertTrue(self.group.valid)


if __name__ == '__main__':
    unittest.main()
