"""python3 -m report <file.csv>"""

from __future__ import annotations

import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from report.expenses import ReportError, read_expenses, summary, totals_by_currency


def format_totals(totals: dict[str, Decimal]) -> list[str]:
    cent = Decimal("0.01")
    return [f"{code} {total.quantize(cent, rounding=ROUND_HALF_UP)}" for code, total in totals.items()]


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: python3 -m report <file.csv>", file=sys.stderr)
        return 2
    try:
        expenses = read_expenses(Path(argv[0]))
    except (OSError, ReportError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(summary(expenses))
    for line in format_totals(totals_by_currency(expenses)):
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
