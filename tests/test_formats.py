import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from report.expenses import Expense, ReportError, read_expenses

EXPECTED = [
    Expense(date(2026, 1, 5), "Coffee", Decimal("4.20"), "USD"),
    Expense(date(2026, 1, 6), "Taxi", Decimal("12.50"), "EUR"),
]


class FormatTests(unittest.TestCase):
    def write(self, name: str, text: str) -> Path:
        d = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: [p.unlink() for p in d.iterdir()] and d.rmdir())
        p = d / name
        p.write_text(text, encoding="utf-8")
        return p

    def test_csv_by_extension(self):
        p = self.write(
            "e.csv",
            "date,description,amount,currency\n"
            "2026-01-05,Coffee,4.20,USD\n2026-01-06,Taxi,12.50,EUR\n",
        )
        self.assertEqual(read_expenses(p), EXPECTED)

    def test_uppercase_extension(self):
        p = self.write(
            "e.CSV",
            "date,description,amount,currency\n2026-01-05,Coffee,4.20,USD\n",
        )
        self.assertEqual(read_expenses(p), EXPECTED[:1])

    def test_json_decimal_exact(self):
        p = self.write(
            "e.json",
            '[{"date":"2026-01-05","description":"Coffee","amount":4.20,"currency":"USD"}]',
        )
        result = read_expenses(p)
        self.assertEqual(result[0].amount, Decimal("4.20"))
        self.assertEqual(str(result[0].amount), "4.20")
        self.assertIsInstance(result[0].day, date)

    def test_xml_matches_csv(self):
        p = self.write(
            "e.xml",
            "<expenses>"
            "<expense><date>2026-01-05</date><description>Coffee</description>"
            "<amount>4.20</amount><currency>USD</currency></expense>"
            "<expense><date>2026-01-06</date><description>Taxi</description>"
            "<amount>12.50</amount><currency>EUR</currency></expense>"
            "</expenses>",
        )
        self.assertEqual(read_expenses(p), EXPECTED)

    def test_unsupported_extension(self):
        for name in ("e.xlsx", "e.txt"):
            with self.subTest(name=name):
                p = self.write(name, "x")
                with self.assertRaisesRegex(ReportError, "unsupported"):
                    read_expenses(p)

    def test_bad_json_record_names_line(self):
        p = self.write(
            "e.json",
            '[{"date":"2026-01-05","description":"a","amount":1,"currency":"USD"},'
            '{"date":"nope","description":"b","amount":1,"currency":"USD"}]',
        )
        with self.assertRaisesRegex(ReportError, "line 2"):
            read_expenses(p)

    def test_malformed_json_and_xml(self):
        for name, text in (("e.json", "[{"), ("e.xml", "<expenses>")):
            with self.subTest(name=name):
                p = self.write(name, text)
                with self.assertRaises(ReportError):
                    read_expenses(p)


if __name__ == "__main__":
    unittest.main()
