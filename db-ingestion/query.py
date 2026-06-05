#!/usr/bin/env python3

# python query.py --query pieces_by_journal
# python query.py --format md --out kopani_report.md
# python query.py --format json --out kopani_report.json
# python query.py --format csv --out query_results
# python query.py --format csv --out query_results

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


DEFAULT_DB_PATH = Path("kopani.sqlite")


@dataclass(frozen=True)
class Query:
    name: str
    title: str
    sql: str
    description: str = ""
    empty_message: str = "No rows returned."


QUERIES: dict[str, Query] = {
    "pieces_by_journal": Query(
        name="pieces_by_journal",
        title="Pieces by Journal",
        description="Counts how many pieces landed for each journal.",
        sql="""
            SELECT
                j.name AS journal,
                COUNT(*) AS piece_count
            FROM pieces p
            JOIN journals j ON j.id = p.journal_id
            GROUP BY j.id, j.name
            ORDER BY piece_count DESC, journal;
        """,
    ),

    "dual_role_contributors": Query(
        name="dual_role_contributors",
        title="Dual-Role Contributors",
        description="Finds contributors listed as both author and translator on the same piece.",
        sql="""
            SELECT DISTINCT
                a.name AS contributor,
                p.title AS piece_title
            FROM piece_contributors pc1
            JOIN piece_contributors pc2
              ON pc1.piece_id = pc2.piece_id
             AND pc1.author_id = pc2.author_id
             AND pc1.role = 'author'
             AND pc2.role = 'translator'
            JOIN pieces p ON p.id = pc1.piece_id
            JOIN authors a ON a.id = pc1.author_id
            ORDER BY contributor, piece_title;
        """,
        empty_message="No dual-role contributors found.",
    ),

    "pieces_with_no_contributors": Query(
        name="pieces_with_no_contributors",
        title="Pieces with No Contributors",
        description="Finds pieces that do not appear in piece_contributors.",
        sql="""
            SELECT
                id,
                title
            FROM pieces
            WHERE id NOT IN (
                SELECT piece_id
                FROM piece_contributors
            )
            ORDER BY id;
        """,
        empty_message="Every piece has at least one contributor.",
    ),

    "other_content_types": Query(
        name="other_content_types",
        title="Raw Content Types Falling into 'Other'",
        description="Shows raw content_type values that were normalized to 'other'.",
        sql="""
            SELECT
                COALESCE(content_type_raw, '(NULL)') AS raw_content_type,
                COUNT(*) AS piece_count,
                original_url, content_type_raw
            FROM pieces
            WHERE content_type = 'other'
            GROUP BY content_type_raw
            ORDER BY piece_count DESC, raw_content_type;
        """,
        empty_message="No pieces currently fall into content_type = 'other'.",
    ),

    "weird_titles": Query(
        name="weird_titles",
        title="Suspicious Titles",
        description="Finds missing, very short, or unusually long titles.",
        sql="""
            SELECT
                pieces.id,
                pieces.title,
                pieces.original_url,
                j.name AS journal,
                length(pieces.title) AS title_length
            FROM pieces
            JOIN journals j
                ON j.id = pieces.journal_id
            WHERE pieces.title IS NULL
            OR length(pieces.title) < 3
            OR length(pieces.title) > 200
            ORDER BY title_length DESC, pieces.id;
        """,
        empty_message="No suspicious titles found.",
    ),

    "author_count": Query(
        name="author_count",
        title="Author Count",
        description="Counts total authors in the authors table.",
        sql="""
            SELECT
                COUNT(*) AS author_count
            FROM authors;
        """,
    ),

    "slug_collisions": Query(
        name="slug_collisions",
        title="Author Slug Collisions",
        description="Finds duplicate author slugs.",
        sql="""
            SELECT
                slug,
                COUNT(*) AS author_count
            FROM authors
            GROUP BY slug
            HAVING COUNT(*) > 1
            ORDER BY author_count DESC, slug;
        """,
        empty_message="No author slug collisions found.",
    ),
    "content_type_distribution": Query(
        name="content_type_distribution",
        title="Content Type Distribution",
        description="Counts pieces by normalized content_type, broken out per journal.",
        sql="""
            SELECT
                j.name                          AS journal,
                COALESCE(p.content_type, '(NULL)') AS content_type,
                COUNT(*)                        AS piece_count,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY j.name), 1)
                                                AS pct_of_journal
            FROM pieces p
            JOIN journals j ON j.id = p.journal_id
            GROUP BY j.name, p.content_type
            ORDER BY j.name, piece_count DESC;
        """,
    ),
    "dek_keyword_coverage": Query(
        name="dek_keyword_coverage",
        title="Dek & Keyword Coverage by Journal",
        description="Per journal: how many pieces have a real dek (summary) and real ai_keywords vs. missing (NULL / empty / 'null' / 'none').",
        sql="""
            SELECT
                j.name AS journal,
                COUNT(*) AS total,
                SUM(CASE
                        WHEN p.summary IS NOT NULL
                         AND TRIM(p.summary) <> ''
                         AND LOWER(TRIM(p.summary)) NOT IN ('null', 'none')
                        THEN 1 ELSE 0
                    END) AS with_dek,
                SUM(CASE
                        WHEN p.summary IS NULL
                          OR TRIM(p.summary) = ''
                          OR LOWER(TRIM(p.summary)) IN ('null', 'none')
                        THEN 1 ELSE 0
                    END) AS no_dek,
                SUM(CASE
                        WHEN p.ai_keywords_json IS NOT NULL
                         AND LOWER(TRIM(p.ai_keywords_json)) NOT IN ('', '[]', 'null', 'none')
                        THEN 1 ELSE 0
                    END) AS with_keywords,
                SUM(CASE
                        WHEN p.ai_keywords_json IS NULL
                          OR LOWER(TRIM(p.ai_keywords_json)) IN ('', '[]', 'null', 'none')
                        THEN 1 ELSE 0
                    END) AS no_keywords
            FROM pieces p
            JOIN journals j ON j.id = p.journal_id
            GROUP BY j.id, j.name
            ORDER BY journal;
        """,
        empty_message="No pieces found.",
    ),
    "top_keywords": Query(
        name="top_keywords",
        title="Top 400 AI Keywords by Frequency",
        description=(
            "Unnests pieces.ai_keywords_json across all pieces and counts how often "
            "each keyword appears. Use to audit whether the AI-derived vocabulary "
            "looks/sounds too Gen-AI. Top 400 by frequency."
        ),
        sql="""
            WITH valid AS (
                SELECT p.ai_keywords_json AS kw
                FROM pieces p
                WHERE p.ai_keywords_json IS NOT NULL
                  AND json_valid(p.ai_keywords_json)
                  AND json_type(p.ai_keywords_json) = 'array'
            )
            SELECT
                TRIM(LOWER(je.value)) AS keyword,
                COUNT(*)             AS frequency,
                COUNT(DISTINCT je.value) AS distinct_casings
            FROM valid v,
                 json_each(v.kw) je
            WHERE je.value IS NOT NULL
              AND TRIM(je.value) <> ''
            GROUP BY keyword
            ORDER BY frequency DESC, keyword
            LIMIT 400;
        """,
        empty_message="No keywords found in ai_keywords_json.",
    )
}


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def fetch_query(conn: sqlite3.Connection, query: Query) -> tuple[list[str], list[sqlite3.Row]]:
    cursor = conn.execute(query.sql)
    rows = cursor.fetchall()
    columns = [description[0] for description in cursor.description or []]
    return columns, rows


def cell_to_text(value: object) -> str:
    if value is None:
        return "NULL"
    return str(value).replace("\n", "\\n")


def truncate(text: str, width: int) -> str:
    if len(text) <= width:
        return text
    if width <= 3:
        return text[:width]
    return text[: width - 3] + "..."


def render_table(
    columns: Sequence[str],
    rows: Sequence[sqlite3.Row],
    max_col_width: int = 60,
) -> str:
    if not columns:
        return ""

    widths: list[int] = []

    for column in columns:
        values = [cell_to_text(row[column]) for row in rows]
        widest = max([len(column), *[len(value) for value in values]])
        widths.append(min(widest, max_col_width))

    def render_row(values: Sequence[object]) -> str:
        parts = []
        for value, width in zip(values, widths):
            text = truncate(cell_to_text(value), width)
            parts.append(text.ljust(width))
        return "| " + " | ".join(parts) + " |"

    border = "+-" + "-+-".join("-" * width for width in widths) + "-+"
    header = render_row(columns)

    lines = [
        border,
        header,
        border,
    ]

    for row in rows:
        lines.append(render_row([row[column] for column in columns]))

    lines.append(border)
    return "\n".join(lines)


def render_screen_section(query: Query, columns: list[str], rows: list[sqlite3.Row]) -> str:
    lines = [
        "",
        query.title,
        "=" * len(query.title),
    ]

    if query.description:
        lines.append(query.description)

    lines.append(f"Rows: {len(rows)}")

    if rows:
        lines.append(render_table(columns, rows))
    else:
        lines.append(query.empty_message)

    return "\n".join(lines)


def markdown_escape(value: object) -> str:
    return cell_to_text(value).replace("|", "\\|").replace("\n", "<br>")


def render_markdown_table(columns: list[str], rows: list[sqlite3.Row]) -> str:
    if not rows:
        return "_No rows returned._"

    header = "| " + " | ".join(columns) + " |"
    divider = "| " + " | ".join("---" for _ in columns) + " |"

    body = []
    for row in rows:
        body.append("| " + " | ".join(markdown_escape(row[column]) for column in columns) + " |")

    return "\n".join([header, divider, *body])


def render_markdown_section(query: Query, columns: list[str], rows: list[sqlite3.Row]) -> str:
    lines = [
        f"## {query.title}",
        "",
    ]

    if query.description:
        lines.extend([query.description, ""])

    lines.append(f"**Rows:** {len(rows)}")
    lines.append("")

    if rows:
        lines.append(render_markdown_table(columns, rows))
    else:
        lines.append(f"_{query.empty_message}_")

    return "\n".join(lines)


def rows_to_dicts(rows: Sequence[sqlite3.Row]) -> list[dict[str, object]]:
    return [dict(row) for row in rows]


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def write_csv(path: Path, columns: list[str], rows: list[sqlite3.Row]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow(dict(row))


def selected_queries(name: str) -> list[Query]:
    if name == "all":
        return list(QUERIES.values())
    return [QUERIES[name]]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run named SQLite checks against the Kopani database."
    )

    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB_PATH,
        help="Path to the SQLite database. Default: kopani.sqlite",
    )

    parser.add_argument(
        "--query",
        choices=["all", *sorted(QUERIES.keys())],
        default="all",
        help="Which query to run. Default: all",
    )

    parser.add_argument(
        "--format",
        choices=["screen", "md", "json", "csv"],
        default="screen",
        help="Output format. Default: screen",
    )

    parser.add_argument(
        "--out",
        type=Path,
        help="Optional output file or directory.",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if not args.db.exists():
        print(f"Database not found: {args.db}", file=sys.stderr)
        return 1

    queries = selected_queries(args.query)

    with connect(args.db) as conn:
        results = []

        for query in queries:
            columns, rows = fetch_query(conn, query)
            results.append((query, columns, rows))

    if args.format == "screen":
        output = "\n".join(
            render_screen_section(query, columns, rows)
            for query, columns, rows in results
        ).strip()

        if args.out:
            write_text(args.out, output + "\n")
            print(f"Wrote report to {args.out}")
        else:
            print(output)

        return 0

    if args.format == "md":
        output = "# Kopani SQLite Query Report\n\n"
        output += "\n\n".join(
            render_markdown_section(query, columns, rows)
            for query, columns, rows in results
        )
        output += "\n"

        if args.out:
            write_text(args.out, output)
            print(f"Wrote Markdown report to {args.out}")
        else:
            print(output)

        return 0

    if args.format == "json":
        payload = {
            query.name: {
                "title": query.title,
                "description": query.description,
                "row_count": len(rows),
                "rows": rows_to_dicts(rows),
            }
            for query, columns, rows in results
        }

        if args.out:
            write_json(args.out, payload)
            print(f"Wrote JSON report to {args.out}")
        else:
            print(json.dumps(payload, indent=2, ensure_ascii=False))

        return 0

    if args.format == "csv":
        if len(results) == 1:
            query, columns, rows = results[0]
            out_path = args.out or Path(f"{query.name}.csv")
            write_csv(out_path, columns, rows)
            print(f"Wrote CSV to {out_path}")
            return 0

        out_dir = args.out or Path("query_results")
        out_dir.mkdir(parents=True, exist_ok=True)

        for query, columns, rows in results:
            write_csv(out_dir / f"{query.name}.csv", columns, rows)

        print(f"Wrote {len(results)} CSV files to {out_dir}")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())