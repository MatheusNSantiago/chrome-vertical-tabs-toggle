import unittest

from chrome_vertical_tabs_toggle_linux.iterables import find


class FindTest(unittest.TestCase):
    def test_returns_the_first_matching_item(self) -> None:
        numbers = [1, 2, 3, 4]

        self.assertEqual(find(numbers, lambda number: number % 2 == 0), 2)

    def test_returns_none_when_no_item_matches(self) -> None:
        numbers = [1, 3, 5]

        self.assertIsNone(find(numbers, lambda number: number % 2 == 0))


if __name__ == "__main__":
    unittest.main()
