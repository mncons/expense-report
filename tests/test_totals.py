import contextlib
import io
import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from report.__main__ import main
from report.expenses import Expense, totals_by_currency


def exp(amount: str, currency: str) -> Expense:
    return Expense(date(2026, 1, 1), "x", Decimal(amount), currency)


class TotalsByCurrencyTest(unittest.TestCase):
    def test_sums_per_currency_never_across(self):
        lines = totals_by_currency([exp("4.20", "EUR"), exp("6.80", "EUR"), exp("5", "USD")])
        self.assertEqual(lines, ["EUR 11.00", "USD 5.00"])

    def test_sorted_by_code(self):
        lines = totals_by_currency([exp("1", "USD"), exp("2", "EUR"), exp("3", "GBP")])
        self.assertEqual(lines, ["EUR 2.00", "GBP 3.00", "USD 1.00"])

    def test_rounding_half_up_and_two_decimals(self):
        lines = totals_by_currency([exp("0.005", "EUR"), exp("210", "GBP")])
        self.assertEqual(lines, ["EUR 0.01", "GBP 210.00"])

    def test_empty(self):
        self.assertEqual(totals_by_currency([]), [])


class CliTotalsTest(unittest.TestCase):
    def test_cli_prints_summary_then_totals(self):
        csv_text = (
            "date,description,amount,currency\n"
            "2026-01-01,a,485.00,usd\n"
            "2026-01-02,b,4.20,EUR\n"
            "2026-01-03,c,210.00,GBP\n"
            "2026-01-04,d,137.70,EUR\n"
        )
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "e.csv"
            path.write_text(csv_text, encoding="utf-8")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = main([str(path)])
        self.assertEqual(code, 0)
        self.assertEqual(
            out.getvalue().splitlines(),
            [
                "4 expenses from 2026-01-01 to 2026-01-04",
                "EUR 141.90",
                "GBP 210.00",
                "USD 485.00",
            ],
        )


if __name__ == "__main__":
    unittest.main()
