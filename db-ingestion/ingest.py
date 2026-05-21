#!/usr/bin/env python3
"""
ingest.py — Populate kopani.sqlite from scraped JSON files.

Usage:
    python3 ingest.py                            # defaults: ./schema.sql, ./kopani.sqlite, ./json/
    python3 ingest.py --db kopani.sqlite --src /path/to/jsons --schema schema.sql

Behavior:
    1. Applies schema.sql (CREATE TABLE IF NOT EXISTS is idempotent).
    2. Seeds the 5 journals.
    3. Walks --src for *.json, detects each file's journal, extracts canonical
       fields via a per-journal adapter, and upserts into pieces / authors /
       piece_contributors. The raw file is preserved in pieces.raw_json.

Idempotent: re-running updates existing rows by original_url.
"""

import argparse
import json
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

JOURNAL_DEFS = [
    {"slug": "the-threepenny-review", "name": "The Threepenny Review",
     "homepage_url": "https://www.threepennyreview.com",
     "country": "United States", "city": "Berkeley",
     "genres": ["essay", "poetry", "fiction"]},
    {"slug": "new-orleans-review", "name": "New Orleans Review",
     "homepage_url": "https://www.neworleansreview.org",
     "country": "United States", "city": "New Orleans",
     "genres": ["poetry", "fiction", "nonfiction", "art"]},
    {"slug": "granta", "name": "Granta",
     "homepage_url": "https://granta.com",
     "country": "United Kingdom", "city": "London",
     "genres": ["essay", "fiction", "poetry", "art"]},
    {"slug": "the-offing", "name": "The Offing",
     "homepage_url": "https://theoffingmag.com",
     "country": "United States", "city": None,
     "genres": ["poetry", "essay", "fiction"]},
    {"slug": "evergreen-review", "name": "Evergreen Review",
     "homepage_url": "https://evergreenreview.com",
     "country": "United States", "city": "New York",
     "genres": ["poetry", "fiction", "nonfiction", "art"]},
]

# Maps a raw content_type/piece_type value (lowercased, trimmed) to the
# canonical value stored in pieces.content_type. Anything not in the map
# falls through to "other" but the raw value is preserved in content_type_raw.
CONTENT_TYPE_MAP = {
    "poetry": "poetry", "poems": "poetry", "poem": "poetry",
    "fiction": "fiction", "short story": "fiction", "short_story": "fiction",
    "flash fiction": "fiction", "flash_fiction": "fiction",
    "essay": "essay",
    "nonfiction": "nonfiction", "non-fiction": "nonfiction",
    "review": "review",
    "book review": "book_review",
    "art review": "art_review",
    "art": "art", "art & photography": "art", "art and photography": "art",
    "interview": "interview",
    "podcast": "podcast", "podcasts": "podcast",
    "table_talk": "table_talk", "table talk": "table_talk",
    "youth portfolio": "youth_portfolio",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def slugify(text: str) -> str:
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text or "untitled"

def coalesce(*vals):
    """Return first value that is not None and not the string 'null'."""
    for v in vals:
        if v is None:
            continue
        if isinstance(v, str) and v.strip().lower() in ("", "null", "none"):
            continue
        return v
    return None

def normalize_content_type(raw):
    if not raw:
        return "other", None
    key = str(raw).strip().lower()
    canonical = CONTENT_TYPE_MAP.get(key, "other")
    return canonical, raw

def parse_reading_time(val):
    """Accepts '1 minute', '10.72', 10.72, '1 min', etc. Returns int minutes or None."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return int(round(float(val)))
    s = str(val).strip().lower()
    if not s or s == "null":
        return None
    m = re.search(r"(\d+(?:\.\d+)?)", s)
    if not m:
        return None
    return int(round(float(m.group(1))))

def estimate_word_count(text):
    if not text:
        return None
    return len(str(text).split())

def detect_journal(d: dict) -> str:
    """Return canonical journal slug for a parsed JSON object."""
    j = d.get("journal")
    if isinstance(j, dict):
        name = j.get("name") or ""
        if j.get("slug"):
            # Normalize a couple of legacy mismatches if any
            return j["slug"]
    elif isinstance(j, str):
        name = j
    else:
        name = ""
    name = name.strip().lower()
    table = {
        "the threepenny review": "the-threepenny-review",
        "threepenny review": "the-threepenny-review",
        "new orleans review": "new-orleans-review",
        "granta": "granta",
        "the offing": "the-offing",
        "offing": "the-offing",
        "evergreen review": "evergreen-review",
    }
    if name in table:
        return table[name]
    raise ValueError(f"Could not detect journal from {d.get('journal')!r}")

# ---------------------------------------------------------------------------
# Per-journal extractors
# Each returns a canonical dict the writer understands.
# ---------------------------------------------------------------------------

def extract_threepenny(d):
    derived = d.get("derived") or {}
    content = d.get("content") or {}
    season = (d.get("issue_season") or "").strip().title() or None
    year = d.get("issue_year")
    display_date = f"{season} {year}" if (season and year) else (str(year) if year else None)

    def _as_list(v):
        if v is None: return []
        if isinstance(v, list): return [x for x in v if x]
        if isinstance(v, str) and v.strip().lower() not in ("", "null"): return [v]
        return []

    contributors = []
    authors = _as_list(d.get("author"))
    for i, name in enumerate(authors, start=1):
        contributors.append({
            "name": name, "role": "author",
            "bio": coalesce(derived.get("author_bio_raw")) if i == 1 else None,
            "order": i,
        })
    translators = _as_list(d.get("translator"))
    for i, name in enumerate(translators, start=1):
        contributors.append({"name": name, "role": "translator", "bio": None, "order": i})

    return {
        "title": d.get("title"),
        "subtitle": None,
        "slug_source": d.get("slug"),
        "original_url": coalesce(d.get("canonical_url"), d.get("final_url"), d.get("piece_url")),
        "content_type_raw": coalesce(derived.get("content_type")),
        "publication_date": None,
        "publication_date_display": display_date,
        "issue_label": display_date,
        "issue_url": None,
        "issue_metadata": {
            "season": season, "year": year,
            "issue_number": d.get("issue_number"),
            "issue_slug": d.get("issue_slug"),
        },
        "meta_description": None,
        "source_image_url": None,
        "read_time_minutes": None,
        "word_count_estimate": estimate_word_count(content.get("text")),
        "ai_keywords": derived.get("piece_keywords") or None,
        "contributors": contributors,
    }

def extract_evergreen(d):
    piece = d.get("piece") or {}
    issue = d.get("issue") or {}
    derived = d.get("derived") or {}
    content = d.get("content") or {}

    season = (derived.get("issue_season") or "").strip().lower()
    season_disp = {"fw": "F/W", "ss": "S/S"}.get(season, season.upper() or None)
    year = derived.get("issue_year")
    display_date = f"{season_disp} {year}" if (season_disp and year) else None

    contributors = []
    # Author(s)
    authors_raw = d.get("authors_raw") or []
    if authors_raw:
        for i, a in enumerate(authors_raw, start=1):
            name = coalesce(a.get("display_name"))
            if not name: continue
            contributors.append({
                "name": name, "role": "author",
                "bio": coalesce(derived.get("author_bio_raw")) if i == 1 else None,
                "order": i,
            })
    elif coalesce(piece.get("author")):
        contributors.append({
            "name": piece["author"], "role": "author",
            "bio": coalesce(derived.get("author_bio_raw")), "order": 1,
        })
    # Translator
    tr = coalesce(piece.get("translator"))
    if tr:
        contributors.append({"name": tr, "role": "translator", "bio": None, "order": 1})
    # Visual artist
    va = coalesce(piece.get("visual_artist"))
    if va:
        contributors.append({
            "name": va, "role": "visual_artist",
            "bio": coalesce(derived.get("visual_artist_bio_raw")), "order": 1,
        })

    content_type_raw = coalesce(piece.get("piece_type"), piece.get("content_type"))

    return {
        "title": coalesce(piece.get("title_display"), piece.get("title_tag")),
        "subtitle": None,
        "slug_source": piece.get("source_slug"),
        "original_url": coalesce(piece.get("originalurl"), piece.get("request_url")),
        "content_type_raw": content_type_raw,
        "publication_date": coalesce(piece.get("date_published_display")),
        "publication_date_display": display_date,
        "issue_label": coalesce(issue.get("issue_label")),
        "issue_url": coalesce(issue.get("issue_url")),
        "issue_metadata": {
            "season": season, "year": year,
            "section": coalesce(issue.get("section_from_issue")),
        },
        "meta_description": coalesce((d.get("page_metadata") or {}).get("meta_description")),
        "source_image_url": None,
        "read_time_minutes": parse_reading_time(derived.get("reading_time")),
        "word_count_estimate": estimate_word_count(content.get("text")),
        "ai_keywords": derived.get("piece_keywords") or None,
        "contributors": contributors,
    }

def extract_granta(d):
    piece = d.get("piece") or {}
    issue = d.get("issue") or {}
    derived = d.get("derived") or {}
    content = d.get("content") or {}

    contributors = []
    authors_raw = d.get("authors_raw") or []
    bios = derived.get("author_bios_raw") or [derived.get("author_bio_raw")]
    for i, a in enumerate(authors_raw, start=1):
        name = coalesce(a.get("display_name"))
        if not name: continue
        bio = coalesce(bios[i-1]) if i-1 < len(bios) else None
        contributors.append({"name": name, "role": "author", "bio": bio, "order": i})
    if not contributors and coalesce(piece.get("author")):
        contributors.append({
            "name": piece["author"], "role": "author",
            "bio": coalesce(derived.get("author_bio_raw")), "order": 1,
        })
    # Translators
    tr_raw = d.get("translators_raw") or []
    tr_bios = derived.get("translator_bios_raw") or [derived.get("translator_bio_raw")]
    for i, t in enumerate(tr_raw, start=1):
        name = coalesce(t.get("display_name"))
        if not name: continue
        bio = coalesce(tr_bios[i-1]) if i-1 < len(tr_bios) else None
        contributors.append({"name": name, "role": "translator", "bio": bio, "order": i})

    return {
        "title": coalesce(piece.get("title_display"), piece.get("title_tag")),
        "subtitle": None,
        "slug_source": piece.get("source_slug"),
        "original_url": coalesce(piece.get("original_url"), piece.get("canonical_url")),
        "content_type_raw": coalesce(piece.get("piece_type")),
        "publication_date": coalesce(piece.get("date_published_display")),  # already YYYY-MM-DD
        "publication_date_display": coalesce(issue.get("issue_date")),
        "issue_label": coalesce(issue.get("issue_label")),
        "issue_url": coalesce(issue.get("issue_url")),
        "issue_metadata": {
            "issue_number": coalesce(issue.get("issue_number")),
            "issue_date": coalesce(issue.get("issue_date")),
            "edition": coalesce(piece.get("edition")),
        },
        "meta_description": coalesce(piece.get("meta_description"),
                                     (d.get("page_metadata") or {}).get("meta_description")),
        "source_image_url": None,
        "read_time_minutes": None,
        "word_count_estimate": estimate_word_count(content.get("text")),
        "ai_keywords": None,
        "contributors": contributors,
    }

def extract_offing(d):
    piece = d.get("piece") or {}
    dept = d.get("department") or {}
    derived = d.get("derived") or {}
    content = d.get("content") or {}

    contributors = []
    authors_raw = d.get("authors_raw") or []
    bios = derived.get("author_bios_raw") or [derived.get("author_bio_raw")]
    for i, a in enumerate(authors_raw, start=1):
        name = coalesce(a.get("display_name"))
        if not name: continue
        bio = coalesce(bios[i-1]) if i-1 < len(bios) else None
        contributors.append({"name": name, "role": "author", "bio": bio, "order": i})
    if not contributors and coalesce(piece.get("author")):
        contributors.append({
            "name": piece["author"], "role": "author",
            "bio": coalesce(derived.get("author_bio_raw")), "order": 1,
        })
    tr_raw = d.get("translators_raw") or []
    tr_bios = derived.get("translator_bios_raw") or [derived.get("translator_bio_raw")]
    for i, t in enumerate(tr_raw, start=1):
        name = coalesce(t.get("display_name"))
        if not name: continue
        bio = coalesce(tr_bios[i-1]) if i-1 < len(tr_bios) else None
        contributors.append({"name": name, "role": "translator", "bio": bio, "order": i})

    return {
        "title": coalesce(piece.get("title_display"), piece.get("title_tag")),
        "subtitle": coalesce(piece.get("subtitle")),
        "slug_source": piece.get("source_slug"),
        "original_url": coalesce(piece.get("original_url"), piece.get("canonical_url")),
        "content_type_raw": coalesce(piece.get("piece_type")),
        "publication_date": coalesce(piece.get("date_published_iso")),
        "publication_date_display": coalesce(piece.get("date_published_display")),
        "issue_label": coalesce(dept.get("name")),       # Offing has departments, not issues
        "issue_url": coalesce(dept.get("department_url")),
        "issue_metadata": {"department": coalesce(dept.get("name"))},
        "meta_description": coalesce(piece.get("meta_description")),
        "source_image_url": coalesce(piece.get("og_image")),
        "read_time_minutes": parse_reading_time(piece.get("reading_time")),
        "word_count_estimate": estimate_word_count(content.get("text")),
        "ai_keywords": None,
        "contributors": contributors,
    }

def extract_nor(d):
    piece = d.get("piece") or {}
    issue = d.get("issue") or {}
    derived = d.get("derived") or {}
    content = d.get("content") or {}

    contributors = []
    authors_raw = d.get("authors_raw") or []
    for i, a in enumerate(authors_raw, start=1):
        name = coalesce(a.get("display_name"))
        if not name: continue
        bio = coalesce(derived.get("author_bio_raw")) if i == 1 else None
        contributors.append({"name": name, "role": "author", "bio": bio, "order": i})
    if not contributors and coalesce(piece.get("author")):
        contributors.append({
            "name": piece["author"], "role": "author",
            "bio": coalesce(derived.get("author_bio_raw")), "order": 1,
        })

    return {
        "title": coalesce(piece.get("title_display"), piece.get("title_tag")),
        "subtitle": None,
        "slug_source": piece.get("source_slug"),
        "original_url": coalesce(piece.get("originalurl"), piece.get("request_url"),
                                 (d.get("page_metadata") or {}).get("canonical_url")),
        "content_type_raw": coalesce(piece.get("piece_type")),
        "publication_date": None,
        "publication_date_display": coalesce(piece.get("date_published_display")),
        "issue_label": coalesce(issue.get("issue_label")),
        "issue_url": coalesce(issue.get("issue_url")),
        "issue_metadata": {
            "issue_label": coalesce(issue.get("issue_label")),
            "section": coalesce(issue.get("section_from_issue")),
            "order_in_section": coalesce(piece.get("order_in_section")),
            "categories": piece.get("categories") or [],
        },
        "meta_description": None,
        "source_image_url": None,
        "read_time_minutes": None,
        "word_count_estimate": estimate_word_count(content.get("text")),
        "ai_keywords": None,
        "contributors": contributors,
    }

EXTRACTORS = {
    "the-threepenny-review": extract_threepenny,
    "evergreen-review": extract_evergreen,
    "granta": extract_granta,
    "the-offing": extract_offing,
    "new-orleans-review": extract_nor,
}

# ---------------------------------------------------------------------------
# Database writers
# ---------------------------------------------------------------------------

def seed_journals(cur):
    for j in JOURNAL_DEFS:
        cur.execute("""
            INSERT INTO journals (slug, name, homepage_url, country, city, genres_supported_json)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(slug) DO UPDATE SET
              name = excluded.name,
              homepage_url = excluded.homepage_url,
              country = excluded.country,
              city = excluded.city,
              genres_supported_json = excluded.genres_supported_json,
              updated_at = datetime('now')
        """, (j["slug"], j["name"], j["homepage_url"], j["country"], j["city"],
              json.dumps(j["genres"])))

def get_journal_id(cur, slug):
    row = cur.execute("SELECT id FROM journals WHERE slug = ?", (slug,)).fetchone()
    return row[0] if row else None

def upsert_author(cur, name, bio):
    """Idempotent author insert. Returns author_id."""
    slug = slugify(name)
    if not slug:
        return None
    # Handle slug collisions by appending name disambiguator (rare)
    row = cur.execute("SELECT id, bio FROM authors WHERE slug = ?", (slug,)).fetchone()
    if row:
        author_id, existing_bio = row
        # Only fill bio if currently empty
        if bio and not existing_bio:
            cur.execute("UPDATE authors SET bio = ?, updated_at = datetime('now') WHERE id = ?",
                        (bio, author_id))
        return author_id
    cur.execute("INSERT INTO authors (name, slug, bio) VALUES (?, ?, ?)", (name, slug, bio))
    return cur.lastrowid

def upsert_piece(cur, journal_id, canonical, raw_text):
    content_type, content_type_raw = normalize_content_type(canonical["content_type_raw"])
    slug = slugify(canonical.get("slug_source") or canonical.get("title") or "")
    title = canonical.get("title") or "(untitled)"
    original_url = canonical.get("original_url")
    if not original_url:
        raise ValueError("piece has no original_url")

    cur.execute("""
        INSERT INTO pieces (
            slug, title, subtitle, journal_id, original_url,
            content_type, content_type_raw, format, meta_description,
            publication_date, publication_date_display,
            word_count_estimate, read_time_minutes,
            source_image_url, issue_label, issue_url, issue_metadata_json,
            ai_keywords_json, ingestion_status, raw_json
        ) VALUES (?, ?, ?, ?, ?,  ?, ?, ?, ?,  ?, ?,  ?, ?,  ?, ?, ?, ?,  ?, ?, ?)
        ON CONFLICT(original_url) DO UPDATE SET
            slug                     = excluded.slug,
            title                    = excluded.title,
            subtitle                 = excluded.subtitle,
            content_type             = excluded.content_type,
            content_type_raw         = excluded.content_type_raw,
            meta_description         = excluded.meta_description,
            publication_date         = excluded.publication_date,
            publication_date_display = excluded.publication_date_display,
            word_count_estimate      = excluded.word_count_estimate,
            read_time_minutes        = excluded.read_time_minutes,
            source_image_url         = excluded.source_image_url,
            issue_label              = excluded.issue_label,
            issue_url                = excluded.issue_url,
            issue_metadata_json      = excluded.issue_metadata_json,
            ai_keywords_json         = excluded.ai_keywords_json,
            ingestion_status         = excluded.ingestion_status,
            raw_json                 = excluded.raw_json,
            updated_at               = datetime('now')
    """, (
        slug, title, canonical.get("subtitle"), journal_id, original_url,
        content_type, content_type_raw, "text/html", canonical.get("meta_description"),
        canonical.get("publication_date"), canonical.get("publication_date_display"),
        canonical.get("word_count_estimate"), canonical.get("read_time_minutes"),
        canonical.get("source_image_url"),
        canonical.get("issue_label"), canonical.get("issue_url"),
        json.dumps(canonical.get("issue_metadata") or {}, ensure_ascii=False),
        json.dumps(canonical.get("ai_keywords")) if canonical.get("ai_keywords") else None,
        "normalized", raw_text,
    ))
    return cur.execute("SELECT id FROM pieces WHERE original_url = ?", (original_url,)).fetchone()[0]

def link_contributors(cur, piece_id, contributors):
    # Clear existing links for this piece (allows re-ingestion to fix mistakes).
    cur.execute("DELETE FROM piece_contributors WHERE piece_id = ?", (piece_id,))
    for c in contributors:
        author_id = upsert_author(cur, c["name"], c.get("bio"))
        if author_id is None:
            continue
        cur.execute("""
            INSERT OR IGNORE INTO piece_contributors (piece_id, author_id, role, display_order)
            VALUES (?, ?, ?, ?)
        """, (piece_id, author_id, c["role"], c.get("order", 1)))

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db",     default="kopani.sqlite")
    ap.add_argument("--src",    default="json")
    ap.add_argument("--schema", default="schema.sql")
    args = ap.parse_args()

    db_path = Path(args.db)
    src_dir = Path(args.src)
    schema_path = Path(args.schema)

    if not schema_path.exists():
        sys.exit(f"schema.sql not found: {schema_path}")
    if not src_dir.exists():
        sys.exit(f"source directory not found: {src_dir}")

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    with open(schema_path) as f:
        conn.executescript(f.read())

    cur = conn.cursor()
    seed_journals(cur)
    conn.commit()

    files = sorted(src_dir.glob("*.json"))
    counts = {"ok": 0, "skipped": 0, "errors": 0}
    per_journal = {}
    errors = []

    for fp in files:
        try:
            with open(fp, encoding="utf-8") as f:
                raw_text = f.read()
            data = json.loads(raw_text)
            journal_slug = detect_journal(data)
            extractor = EXTRACTORS[journal_slug]
            canonical = extractor(data)
            journal_id = get_journal_id(cur, journal_slug)
            piece_id = upsert_piece(cur, journal_id, canonical, raw_text)
            link_contributors(cur, piece_id, canonical["contributors"])
            counts["ok"] += 1
            per_journal[journal_slug] = per_journal.get(journal_slug, 0) + 1
        except Exception as e:
            counts["errors"] += 1
            errors.append((fp.name, str(e)))

    conn.commit()
    conn.close()

    print(f"\nIngest complete -> {db_path}")
    print(f"  ok:      {counts['ok']}")
    print(f"  errors:  {counts['errors']}")
    print("  per journal:")
    for k, v in sorted(per_journal.items()):
        print(f"    {k:25s} {v}")
    if errors:
        print("\n  first 10 errors:")
        for name, msg in errors[:10]:
            print(f"    {name}: {msg}")

if __name__ == "__main__":
    main()
