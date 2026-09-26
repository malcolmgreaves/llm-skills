import unittest

from cells import address


class AddressTest(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(address.parse("A1"), (1, 1))
        self.assertEqual(address.parse("B12"), (2, 12))
        self.assertEqual(address.parse("Z3"), (26, 3))

    def test_lowercase(self):
        self.assertEqual(address.parse("c4"), (3, 4))

    def test_invalid(self):
        for text in ("", "A", "1", "A0", "1A", "A1B", "A-1"):
            with self.assertRaises(ValueError):
                address.parse(text)

    def test_name(self):
        self.assertEqual(address.name(2, 12), "B12")
        self.assertEqual(address.name(26, 1), "Z1")
        self.assertEqual(address.name(27, 1), "AA1")


if __name__ == "__main__":
    unittest.main()
