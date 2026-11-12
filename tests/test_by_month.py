import subprocess
import sys
import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from report.expenses import Expense, totals_by_month

HEADER = "date,description,amount,currency\n"


def exp(day: str, amount: str, cur: str = "USD") -> Expense:
    return Expense(date.fromisoformat(day), "x", Decimal(amount), cur)


def write_csv(text: str) -> Path:
    f = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8")
    f.write(text)
    f.close()
    return Path(f.name)


class TotalsByMonth(unittest.TestCase):
    def test_same_month_and_currency_summed(self) -> None:
        r = totals_by_month([exp("2026-10-01", "1.50"), exp("2026-10-20", "2.00")])
        self.assertEqual(r, {"2026-10": {"USD": Decimal("3.50")}})

    def test_currencies_stay_separate(self) -> None:
        r = totals_by_month([exp("2026-10-01", "1", "USD"), exp("2026-10-02", "2", "EUR")])
        self.assertEqual(r["2026-10"], {"USD": Decimal("1"), "EUR": Decimal("2")})

    def test_chronological_across_year_boundary(self) -> None:
        r = totals_by_month([exp("2026-01-05", "1"), exp("2025-12-31", "1"), exp("2026-03-01", "1")])
        self.assertEqual(list(r), ["2025-12", "2026-01", "2026-03"])

    def test_key_is_zero_padded(self) -> None:
        self.assertEqual(list(totals_by_month([exp("2026-03-09", "1")])), ["2026-03"])

    def test_empty(self) -> None:
        self.assertEqual(totals_by_month([]), {})

    def test_decimal_exact(self) -> None:
        r = totals_by_month([exp("2026-10-01", "0.10"), exp("2026-10-02", "0.20")])
        total = r["2026-10"]["USD"]
        self.assertIsInstance(total, Decimal)
        self.assertEqual(total, Decimal("0.30"))


class ByMonthCli(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, "-m", "report", *args], capture_output=True, text=True)

    def test_sample_blocks(self) -> None:
        out = self.run_cli("data/sample.csv", "--by-month")
        self.assertEqual(out.returncode, 0, out.stderr)
        head, _, s = out.stdout.partition("\n")
        self.assertIn("expenses from", head)
        self.assertLess(s.index("2026-09\n"), s.index("2026-10\n"))
        sep, octo = s[s.index("2026-09\n"):s.index("2026-10\n")], s[s.index("2026-10\n"):]
        self.assertIn("EUR 11.00", sep)
        self.assertIn("USD 470.00", sep)
        for line in ("EUR 130.90", "GBP 210.00", "USD 15.00"):
            self.assertIn(line, octo)

    def test_half_up_at_print_time(self) -> None:
        path = write_csv(HEADER + "2026-10-01,a,0.002,USD\n2026-10-02,b,0.003,USD\n")
        out = self.run_cli(str(path), "--by-month")
        self.assertIn("USD 0.01", out.stdout)

    def test_without_flag_only_summary(self) -> None:
        out = self.run_cli("data/sample.csv")
        self.assertEqual(len(out.stdout.strip().splitlines()), 1)
        self.assertNotIn("USD", out.stdout)

    def test_flag_before_file(self) -> None:
        out = self.run_cli("--by-month", "data/sample.csv")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("2026-09\n", out.stdout)

    def test_unknown_flag_exits_2(self) -> None:
        out = self.run_cli("data/sample.csv", "--bogus")
        self.assertEqual(out.returncode, 2)
        self.assertIn("usage", out.stderr)

    def test_bad_file_exits_1(self) -> None:
        self.assertEqual(self.run_cli("missing.csv", "--by-month").returncode, 1)

    def test_empty_input(self) -> None:
        out = self.run_cli(str(write_csv(HEADER)), "--by-month")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertEqual(out.stdout.strip(), "No expenses.")


if __name__ == "__main__":
    unittest.main()
