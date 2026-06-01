#!/usr/bin/env python3
"""
Migration: normalize content_type 'nonfiction' -> 'essay'.

Run from the same folder as ingest.py / kopani.sqlite:

    python migrate_nonfiction_to_essay.py            # preview only (dry run)
    python migrate_nonfiction_to_essay.py --apply    # actually write changes
    python migrate_nonfiction_to_essay.py --apply --db path/to/kopani.sqlite

Safety:
  * Defaults to a DRY RUN. Nothing is written unless you pass --apply.
  * Writes a timestamped .bak copy of the DB before applying.
  * content_type_raw is left untouched, so the original source value is
    preserved for audit and the change is fully reversible.
  * Idempotent: running it twice does nothing the second time.
"""

from __future__ import annotations

import argparse
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

DEFAULT_DB_PATH = Path("kopani.sqlite")
FROM_TYPE = "nonfiction"
TO_TYPE   = "essay"


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def preview(conn: sqlite3.Connection) -> int:
    """Show what will change. Returns the count of affected rows."""
    rows = conn.execute(
        """
        SELECT j.name AS journal,
               COALESCE(p.content_type_raw, '(NULL)') AS raw,
               COUNT(*) AS n
        FROM pieces p
        JOIN journals j ON j.id = p.journal_id
        WHERE p.content_type = ?
        GROUP BY j.name, p.content_type_raw
        ORDER BY j.name, n DESC;
        """,
        (FROM_TYPE,),
    ).fetchall()

    total = sum(r["n"] for r in rows)

    if total == 0:
        print(f"No pieces with content_type = '{FROM_TYPE}'. Nothing to do.")
        return 0

    print(f"Pieces that will change from '{FROM_TYPE}' -> '{TO_TYPE}':\n")
    print(f"  {'journal':<24} {'content_type_raw':<22} count")
    print(f"  {'-'*24} {'-'*22} -----")
    for r in rows:
        print(f"  {r['journal']:<24} {r['raw']:<22} {r['n']}")
    print(f"\n  TOTAL: {total} pieces")
    return total


def backup_db(db_path: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = db_path.with_name(f"{db_path.stem}.{stamp}.bak{db_path.suffix}")
    shutil.copy2(db_path, bak)
    print(f"Backup written -> {bak}")
    return bak


def apply_migration(conn: sqlite3.Connection) -> int:
    cur = conn.execute(
        """
        UPDATE pieces
        SET content_type = ?,
            updated_at   = datetime('now')
        WHERE content_type = ?;
        """,
        (TO_TYPE, FROM_TYPE),
    )
    conn.commit()
    return cur.rowcount


def main() -> None:
    parser = argparse.ArgumentParser(
        description=f"Normalize content_type '{FROM_TYPE}' -> '{TO_TYPE}' in kopani.sqlite."
    )
    parser.add_argument(
        "--db", type=Path, default=DEFAULT_DB_PATH,
        help=f"Path to SQLite database (default: {DEFAULT_DB_PATH})",
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="Actually write the change. Without this flag, runs as a dry run.",
    )
    args = parser.parse_args()

    if not args.db.exists():
        print(f"Database not found: {args.db}", file=sys.stderr)
        raise SystemExit(1)

    conn = connect(args.db)
    try:
        total = preview(conn)

        if total == 0:
            return

        if not args.apply:
            print("\nDRY RUN — no changes made. Re-run with --apply to commit.")
            return

        conn.close()                 # close before copying the file
        backup_db(args.db)
        conn = connect(args.db)       # reopen for the write

        changed = apply_migration(conn)
        print(f"\nDone. Updated {changed} pieces: '{FROM_TYPE}' -> '{TO_TYPE}'.")

        # Verify
        remaining = conn.execute(
            "SELECT COUNT(*) FROM pieces WHERE content_type = ?;",
            (FROM_TYPE,),
        ).fetchone()[0]
        now_essay = conn.execute(
            "SELECT COUNT(*) FROM pieces WHERE content_type = ?;",
            (TO_TYPE,),
        ).fetchone()[0]
        print(f"Verify: '{FROM_TYPE}' remaining = {remaining}, "
              f"'{TO_TYPE}' total now = {now_essay}.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()