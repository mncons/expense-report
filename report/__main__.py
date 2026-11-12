"""python3 -m report <file.csv> [--by-month]"""

from __future__ import annotations

import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from report.expenses import ReportError, read_expenses, summary, totals_by_month

USAGE = "usage: python3 -m report <file.csv> [--by-month]"


def format_by_month(totals: dict[str, dict[str, Decimal]]) -> list[str]:
    lines: list[str] = []
    for month, currencies in totals.items():
        lines.append(month)
        for code in sorted(currencies):
            amount = currencies[code].quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            lines.append(f"  {code} {amount}")
    return lines


def main(argv: list[str]) -> int:
    by_month = "--by-month" in argv
    paths = [a for a in argv if a != "--by-month"]
    if len(paths) != 1 or paths[0].startswith("--") or argv.count("--by-month") > 1:
        print(USAGE, file=sys.stderr)
        return 2
    try:
        expenses = read_expenses(Path(paths[0]))
    except (OSError, ReportError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(summary(expenses))
    if by_month:
        for line in format_by_month(totals_by_month(expenses)):
            print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
