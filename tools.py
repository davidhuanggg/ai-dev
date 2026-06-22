"""
Tools the agent can call.

The only tool here is `query_data`, which runs a read-only SQL query against the
programs dataset. The CSV is loaded into an in-memory SQLite database so you can
use plain SQL (the same skill you'd use against PostgreSQL in production).

The database plumbing (`load_programs_db`) is done for you. Your job is to make
`query_data` safe and robust -- see the TODOs.
"""

from __future__ import annotations

import csv
import sqlite3
from pathlib import Path
from typing import List

DATA_PATH = Path(__file__).resolve().parent / "data" / "programs.csv"

COLUMNS = [
    ("program_id", "TEXT"),
    ("program_name", "TEXT"),
    ("region", "TEXT"),
    ("sector", "TEXT"),
    ("year", "INTEGER"),
    ("budget_usd", "INTEGER"),
    ("people_served", "INTEGER"),
    ("status", "TEXT"),
]


def load_programs_db(csv_path: Path = DATA_PATH) -> sqlite3.Connection:
    """Load the CSV into a fresh in-memory SQLite DB and return the connection."""
    con = sqlite3.connect(":memory:")
    col_defs = ", ".join(f"{name} {sqltype}" for name, sqltype in COLUMNS)
    con.execute(f"CREATE TABLE programs ({col_defs})")
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        names = [c[0] for c in COLUMNS]
        placeholders = ", ".join("?" for _ in names)
        con.executemany(
            f"INSERT INTO programs VALUES ({placeholders})",
            [tuple(row[n] for n in names) for row in reader],
        )
    return con


def query_data(sql: str, con: sqlite3.Connection | None = None) -> List[list]:
    """
    Run a read-only SQL query against the `programs` table and return rows.

    TODO(candidate):
      1. Validate the input: reject anything that is not a single read-only
         SELECT statement (no INSERT/UPDATE/DELETE/DROP/PRAGMA/ATTACH/;-chaining).
      2. Execute the query and return the rows as a list of lists.
      3. Handle errors gracefully -- a bad query should not crash the agent.
         Decide what `query_data` returns or raises on failure, and make sure
         the agent loop can recover from it.
    """
    raise NotImplementedError("Implement query_data (see TODOs).")
