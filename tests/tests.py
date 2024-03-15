import unittest

from telegram_M_bot.main import add_expense, add_old_expense
from telegram_M_bot.stats import get_costs_by_category, get_costs_per_day


class TestMain(unittest.TestCase):
    def test_add_expense(self):
        # Test the add_expense function
        result = add_expense("test", "food", "yes", 100)
        self.assertEqual(result, "Your expense has been added")

    def test_add_old_expense(self):
        # Test the add_old_expense function
        result = add_old_expense("test", "food", "yes", 100, "01.01.2022")
        self.assertEqual(result, "Your old expense has been added")

    def test_add_expense_negative_amount(self):
        # Test the add_expense function with a negative amount
        result = add_expense("test", "food", "yes", -100)
        self.assertEqual(result, "Invalid amount. It should be a positive number.")

    def test_add_old_expense_invalid_date(self):
        # Test the add_old_expense function with an invalid date
        result = add_old_expense("test", "food", "yes", 100, "invalid_date")
        self.assertEqual(result, "Invalid date. Please enter a valid date in the format dd.mm.yyyy.")


class TestStats(unittest.TestCase):
    def test_get_costs_by_category(self):
        # Test the get_costs_by_category function
        data = [("01.01.2022", "food", 100), ("02.01.2022", "cosmetics", 50)]
        result = get_costs_by_category(data)
        self.assertEqual(result, {"food": 100, "cosmetics": 50})

    def test_get_costs_per_day(self):
        # Test the get_costs_per_day function
        data = [("01.01.2022", "food", 100), ("02.01.2022", "cosmetics", 50)]
        result = get_costs_per_day(data)
        self.assertEqual(result, {1: 100, 2: 50})

    def test_get_costs_by_category_empty_data(self):
        # Test the get_costs_by_category function with empty data
        data = []
        result = get_costs_by_category(data)
        self.assertEqual(result, {})

    def test_get_costs_per_day_single_day(self):
        # Test the get_costs_per_day function with data for a single day
        data = [("01.01.2022", "food", 100), ("01.01.2022", "cosmetics", 50)]
        result = get_costs_per_day(data)
        self.assertEqual(result, {1: 150})


if __name__ == "__main__":
    unittest.main()
