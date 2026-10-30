"""Build the Capacity Fee Workbook (tab 2 as an Excel file) from a tariff file.

    python build_workbook.py [tariff file] [-o excel/capacity_fee_calculator.xlsx]

The tariff file defaults to the committed real export. Run it again after each
new export; a file the app rejects stops the build and writes nothing."""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from core import points, tariffs
from core.workbook import WorkbookError, build_workbook

DEFAULT_OUTPUT = Path(__file__).resolve().parent / "excel" / "capacity_fee_calculator.xlsx"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("tariff_file", nargs="?", type=Path, default=tariffs.DEFAULT_PATH)
    parser.add_argument("-o", "--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)

    result = tariffs.load_tariffs(args.tariff_file)
    for message in result.warnings:
        print(f"Warning: {message}")
    if not result.ok:
        for message in result.errors:
            print(message, file=sys.stderr)
        return 1
    try:
        workbook = build_workbook(result.table, points.build_catalog(result.table), args.tariff_file.name, date.today())
    except WorkbookError as error:
        print(error, file=sys.stderr)
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(args.output)
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
