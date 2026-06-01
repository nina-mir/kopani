#!/usr/bin/env python3
"""
Extract contributor ↔ university associations from raw_json bio insights.

Usage:
    python extract_universities.py
    python extract_universities.py --db path/to/kopani.sqlite
    python extract_universities.py --out my-output.json

Produces contributor-universities.json (flat records) and prints a
per-university summary to stdout.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from collections import defaultdict
from pathlib import Path

DEFAULT_DB_PATH = Path("kopani.sqlite")
DEFAULT_OUT     = Path("contributor-universities.json")

# ── insight key → contributor role ──────────────────────────────────
INSIGHT_ROLE_MAP = {
    "author_bio_insights":        "author",
    "translator_bio_insights":    "translator",
    "visual_artist_bio_insights": "visual_artist",
}

# ── university field → relationship label ───────────────────────────
UNI_FIELDS = {
    "universities_studied_at": "studied",
    "universities_taught_at":  "worked",
}


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def contributors_for_piece(
    conn: sqlite3.Connection, piece_id: int
) -> dict[str, list[str]]:
    """Return {role: [name, ...]} for a piece, ordered by display_order."""
    rows = conn.execute(
        """
        SELECT a.name, pc.role
        FROM piece_contributors pc
        JOIN authors a ON a.id = pc.author_id
        WHERE pc.piece_id = ?
        ORDER BY pc.role, pc.display_order
        """,
        (piece_id,),
    ).fetchall()
    by_role: dict[str, list[str]] = defaultdict(list)
    for r in rows:
        by_role[r["role"]].append(r["name"])
    return dict(by_role)


def extract_records(conn: sqlite3.Connection) -> list[dict]:
    pieces = conn.execute(
        """
        SELECT p.id, p.title, p.raw_json, j.name AS journal_name
        FROM pieces p
        JOIN journals j ON j.id = p.journal_id
        """
    ).fetchall()

    records: list[dict] = []

    for piece in pieces:
        try:
            blob = json.loads(piece["raw_json"])
        except (json.JSONDecodeError, TypeError):
            continue

        derived = blob.get("derived") or {}
        if not isinstance(derived, dict):
            continue

        contribs = contributors_for_piece(conn, piece["id"])

        for insight_key, role in INSIGHT_ROLE_MAP.items():
            insights = derived.get(insight_key)
            if not insights or not isinstance(insights, list):
                continue

            names = contribs.get(role, [])

            for idx, ins in enumerate(insights):
                if not isinstance(ins, dict):
                    continue

                # Best-effort name: match by list position, fall back to
                # the first contributor of that role, or "Unknown".
                name = (
                    names[idx] if idx < len(names)
                    else names[0] if names
                    else "Unknown"
                )

                for uni_field, relationship in UNI_FIELDS.items():
                    unis = ins.get(uni_field)
                    if not unis or not isinstance(unis, list):
                        continue
                    for uni in unis:
                        if not uni or not isinstance(uni, str):
                            continue
                        records.append({
                            "contributor": name,
                            "role": role,
                            "university": uni.strip(),
                            "relationship": relationship,
                            "journal": piece["journal_name"],
                            "pieceTitle": piece["title"],
                        })

    return records


def summarize(records: list[dict]) -> list[dict]:
    """Per-university summary with counts."""
    by_uni: dict[str, dict] = {}

    for r in records:
        uni = r["university"]
        if uni not in by_uni:
            by_uni[uni] = {
                "university": uni,
                "contributors": set(),
                "authors": set(),
                "translators": set(),
                "visualArtists": set(),
                "studied": set(),
                "taught": set(),
            }
        entry = by_uni[uni]
        name = r["contributor"]
        entry["contributors"].add(name)
        if r["role"] == "author":
            entry["authors"].add(name)
        elif r["role"] == "translator":
            entry["translators"].add(name)
        elif r["role"] == "visual_artist":
            entry["visualArtists"].add(name)
        if r["relationship"] == "studied":
            entry["studied"].add(name)
        else:
            entry["taught"].add(name)

    out = []
    for uni in sorted(by_uni):
        e = by_uni[uni]
        out.append({
            "university": uni,
            "contributorCount": len(e["contributors"]),
            "authorCount": len(e["authors"]),
            "translatorCount": len(e["translators"]),
            "visualArtistCount": len(e["visualArtists"]),
            "studiedCount": len(e["studied"]),
            "taughtCount": len(e["taught"]),
            "sampleContributors": sorted(e["contributors"])[:3],
        })
    return sorted(out, key=lambda x: x["contributorCount"], reverse=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract contributor–university associations from Kopani DB."
    )
    parser.add_argument(
        "--db", type=Path, default=DEFAULT_DB_PATH,
        help=f"Path to SQLite database (default: {DEFAULT_DB_PATH})",
    )
    parser.add_argument(
        "--out", type=Path, default=DEFAULT_OUT,
        help=f"Output JSON path (default: {DEFAULT_OUT})",
    )
    args = parser.parse_args()

    if not args.db.exists():
        print(f"Database not found: {args.db}", file=sys.stderr)
        raise SystemExit(1)

    with connect(args.db) as conn:
        records = extract_records(conn)

    # Write flat records
    args.out.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(records)} records → {args.out}")

    # Print summary
    summary = summarize(records)
    print(f"\n{'='*60}")
    print(f"University Summary  ({len(summary)} universities found)")
    print(f"{'='*60}")
    for s in summary:
        print(
            f"\n  {s['university']}"
            f"\n    contributors: {s['contributorCount']}"
            f"  (authors {s['authorCount']}, translators {s['translatorCount']}, "
            f"visual artists {s['visualArtistCount']})"
            f"\n    studied: {s['studiedCount']}, taught/worked: {s['taughtCount']}"
            f"\n    sample: {', '.join(s['sampleContributors'])}"
        )

    # Also write the summary file
    summary_path = args.out.with_stem(args.out.stem + "-summary")
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nWrote summary → {summary_path}")


if __name__ == "__main__":
    import sys
    main()