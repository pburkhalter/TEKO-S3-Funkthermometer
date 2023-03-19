import unittest
from decoder import SignalPart


class TestSignalPart(unittest.TestCase):
    def setUp(self):
        self.part = SignalPart()

    def test_append(self):
        # Arrange
        expected_bits = [1, 0, 0, 1]

        # Act
        for bit in expected_bits:
            self.part.append(bit)

        # Assert
        self.assertEqual(self.part._bits, expected_bits)

    def test_delete(self):
        # Arrange
        bits = [1, 0, 0, 1]
        self.part._bits = bits.copy()

        expected_bits = [1, 0, 1]

        # Act
        self.part.delete(2)

        # Assert
        self.assertEqual(self.part._bits, expected_bits)

    def test_validate_valid(self):
        # Arrange
        bits = [1] * 36
        self.part._bits = bits.copy()

        # Act
        is_valid = self.part.validate()

        # Assert
        self.assertTrue(is_valid)
        self.assertTrue(self.part._validated)

    def test_validate_invalid(self):
        # Arrange
        bits = [1] * 35
        self.part._bits = bits.copy()

        # Act
        is_valid = self.part.validate()

        # Assert
        self.assertFalse(is_valid)
        self.assertFalse(self.part._validated)


if __name__ == '__main__':
    unittest.main()
