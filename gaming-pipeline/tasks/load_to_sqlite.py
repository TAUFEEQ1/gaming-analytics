"""Create an SQLite database and load CSV datasets into separate tables.

Loads:
- `data/interesting_data.csv` -> table `interesting_data`
- any `*with_rolling*.csv` files under `output/` -> table `rolling_<window>` or derived name

Usage:
    python -m tasks.load_to_sqlite --db output/gaming_metrics.db
"""
from __future__ import annotations

import argparse
import re
import sqlite3
from pathlib import Path
import sys
import pandas as pd


def table_name_for_rolling(path: Path) -> str:
    """Derive a compact table name from a rolling CSV filename.

    Examples:
      resampled_15min_windows_with_rolling.csv -> rolling_15min
      resampled_60min_windows_with_rolling.csv -> rolling_60min
    """
    name = path.stem
    m = re.search(r'resampled_(\d+)min', name)
    if m:
        return f"rolling_{m.group(1)}min"
    # fallback: sanitize stem
    sanitized = re.sub(r'[^0-9a-zA-Z_]', '_', name)
    return f"rolling_{sanitized}"


def load_csv_to_table(conn: sqlite3.Connection, csv_path: Path, table_name: str) -> int:
    df = pd.read_csv(csv_path, parse_dates=['time'])
    # Ensure column names are sqlite-friendly
    df.columns = [c.replace(' ', '_') for c in df.columns]
    df.to_sql(table_name, conn, if_exists='replace', index=False)
    return len(df)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Load CSVs into an SQLite database')
    parser.add_argument('--db', default='output/gaming_metrics.db', help='Path to SQLite DB file')
    parser.add_argument('--data-csv', default='data/interesting_data.csv', help='CSV path for interesting data')
    parser.add_argument('--output-dir', default='output', help='Directory to search for rolling CSVs')
    args = parser.parse_args(argv)

    db_path = Path(args.db)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Connect to sqlite
    conn = sqlite3.connect(str(db_path))
    try:
        # Load interesting data
        id_path = Path(args.data_csv)
        if not id_path.exists():
            print(f"Warning: interesting data CSV not found at {id_path}")
        else:
            n = load_csv_to_table(conn, id_path, 'interesting_data')
            print(f"Loaded {n} rows into table `interesting_data`")

        # Find rolling CSVs
        out_dir = Path(args.output_dir)
        if not out_dir.exists():
            print(f"Warning: output directory {out_dir} does not exist; no rolling files loaded")
        else:
            # pick up files that follow the "*_with_*.csv" convention
            rolling_files = sorted(out_dir.rglob('*with_*.csv'))
            if not rolling_files:
                print('No rolling CSV files found under', out_dir)
            for p in rolling_files:
                tbl = table_name_for_rolling(p)
                n = load_csv_to_table(conn, p, tbl)
                print(f"Loaded {n} rows from {p} into table `{tbl}`")

        print(f"Database created at: {db_path.resolve()}")
    finally:
        conn.close()

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
