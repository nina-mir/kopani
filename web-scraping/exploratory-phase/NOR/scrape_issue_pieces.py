# How to run : 
# # Normal resume-safe run:
# ===============================
# $ python scrape_issue_pieces.py piece_urls.json --outdir pieces_json --min-delay 2.0 --max-delay 4.0
# ===============================
# Force a full re-scrape and overwrite:
# ===============================
# $ python scrape_issue_pieces.py piece_urls.json --outdir pieces_json --min-delay 2.0 --max-delay 4.0 --force
# 
# If any page fails, the script now writes _failures.json in the output directory so you can rerun only 
# the missing pieces later. That helps keep the scraping process repeatable and manageable instead of forcing you
# to inspect terminal scrollback.


import argparse
import hashlib
import json
import random
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup, Tag

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; NORExploratoryScraper/0.2; +https://example.com)",
    "Accept-Language": "en-US,en;q=0.9",
}


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def slug_from_url(url: str) -> str:
    path = urlparse(url).path.strip("/")
    return path.split("/")[-1] or "piece"


def make_output_filename_from_url(url: str, idx: int) -> str:
    raw_slug = slug_from_url(url)
    safe_slug = re.sub(r"[^a-zA-Z0-9-]+", "-", raw_slug).strip("-").lower()
    short_slug = safe_slug[:80] if safe_slug else f"piece-{idx}"
    url_hash = hashlib.sha1(url.encode("utf-8")).hexdigest()[:10]
    return f"{short_slug}-{url_hash}.json"


def get_soup(session: requests.Session, url: str) -> BeautifulSoup:
    resp = session.get(url, timeout=30)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "lxml")


def extract_canonical(soup: BeautifulSoup, fallback_url: str) -> str:
    node = soup.select_one('link[rel="canonical"]')
    href = node.get("href", "").strip() if node else ""
    return href or fallback_url


def extract_header(soup: BeautifulSoup):
    title_node = soup.select_one("h1.entry-title") or soup.select_one("main h1")
    meta_node = soup.select_one("p.entry-meta")

    title_display = clean_text(title_node.get_text(" ", strip=True)) if title_node else None
    title_tag = clean_text(soup.title.get_text()) if soup.title else None

    author_nodes = []
    if meta_node:
        for a in meta_node.select('a[href*="/writer/"]'):
            author_nodes.append(
                {
                    "display_name": clean_text(a.get_text(" ", strip=True)),
                    "author_url": a.get("href", "").strip() or None,
                }
            )

    categories = []
    if meta_node:
        for a in meta_node.select(".entry-categories a[href]"):
            categories.append(clean_text(a.get_text(" ", strip=True)))

    return {
        "title_display": title_display,
        "title_tag": title_tag,
        "authors_raw": author_nodes,
        "categories": categories,
    }


def extract_content_node(soup: BeautifulSoup) -> Tag | None:
    selectors = [
        "article .entry-content",
        "main article .entry-content",
        "main article",
        "article",
        "main",
    ]
    for selector in selectors:
        node = soup.select_one(selector)
        if node:
            return node
    return None


def extract_main_text(soup: BeautifulSoup):
    main_node = soup.select_one("main") or extract_content_node(soup)
    if not main_node:
        return None, None
    html = str(main_node)
    text = clean_text(main_node.get_text("\n", strip=True))
    return html, text


def infer_piece_type(categories, section_from_issue):
    cats = " | ".join(categories).lower()
    section = (section_from_issue or "").lower()

    if "interview" in cats or "interview" in section:
        return "interview"
    if "poetry" in cats or "poetry" in section:
        return "poetry"
    if "essay" in cats or "nonfiction" in section:
        return "nonfiction"
    if "fiction" in cats or "fiction" in section:
        return "fiction"
    if "art" in cats or "art" in section:
        return "art"
    return "unknown"


def extract_breadcrumbs(soup: BeautifulSoup):
    crumbs = []
    for node in soup.select(".breadcrumb [itemprop='name']"):
        txt = clean_text(node.get_text(" ", strip=True))
        if txt:
            crumbs.append(txt)
    return crumbs


def extract_json_ld(soup: BeautifulSoup):
    items = []
    for node in soup.select('script[type="application/ld+json"]'):
        raw = node.string or node.get_text()
        raw = raw.strip() if raw else ""
        if not raw:
            continue
        try:
            items.append(json.loads(raw))
        except Exception:
            items.append(raw)
    return items


def detect_bio_paragraph(main_node: Tag | None, authors_raw, piece_type: str):
    if not main_node:
        return None

    paragraphs = [p for p in main_node.select("p") if clean_text(p.get_text(" ", strip=True))]
    if not paragraphs:
        return None

    last_text = clean_text(paragraphs[-1].get_text(" ", strip=True))
    if len(last_text) < 40:
        return None

    author_names = [a.get("display_name", "") for a in authors_raw if a.get("display_name")]
    bio_signal = any(
        name.split()[0].lower() in last_text.lower()
        for name in author_names
        if name and name.split()
    )
    cue_signal = any(
        last_text.lower().startswith(prefix)
        for prefix in ["bio:", "artist statement:"]
    )

    if bio_signal or cue_signal:
        return last_text

    if piece_type in {"fiction", "nonfiction", "poetry", "interview"} and len(last_text.split()) >= 15:
        return last_text

    return None


def extract_subworks(main_node: Tag | None, piece_type: str):
    if piece_type != "poetry" or not main_node:
        return []

    subworks = []
    seen = set()

    for h in main_node.select("h2, h3, h4"):
        title = clean_text(h.get_text(" ", strip=True))
        if not title:
            continue
        key = title.lower()
        if key in seen:
            continue
        seen.add(key)
        subworks.append({"title": title})

    return subworks


def scrape_piece(session: requests.Session, item: dict, issue_url: str):
    url = item["piece_url"]
    section = item.get("section")
    soup = get_soup(session, url)

    canonical_url = extract_canonical(soup, url)
    header = extract_header(soup)
    main_node = soup.select_one("main") or extract_content_node(soup)
    content_html, text_content = extract_main_text(soup)
    piece_type = infer_piece_type(header["categories"], section)

    record = {
        "journal": {
            "name": "New Orleans Review",
            "slug": "new-orleans-review",
        },
        "issue": {
            "issue_url": issue_url,
            "issue_label": next((c for c in header["categories"] if c.isdigit()), None),
            "section_from_issue": section,
        },
        "piece": {
            "originalurl": canonical_url,
            "request_url": url,
            "source_slug": slug_from_url(canonical_url),
            "title_display": header["title_display"],
            "title_tag": header["title_tag"],
            "piece_type": piece_type,
            "categories": header["categories"],
            "link_text_raw": item.get("link_text_raw"),
            "order_in_section": item.get("order_in_section"),
        },
        "authors_raw": header["authors_raw"],
        "content": {
            "text": text_content,
            "html": content_html,
            "subworks": extract_subworks(main_node, piece_type),
        },
        "page_metadata": {
            "canonical_url": canonical_url,
            "breadcrumbs": extract_breadcrumbs(soup),
            "json_ld": extract_json_ld(soup),
        },
        "derived": {
            "author_bio_raw": detect_bio_paragraph(main_node, header["authors_raw"], piece_type),
        },
        "scrape_meta": {
            "scraped_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "scraper_version": "0.2",
            "notes": [],
        },
    }

    if not record["piece"]["title_display"]:
        record["scrape_meta"]["notes"].append("Missing visible title; fell back to title tag or null.")

    if not record["authors_raw"]:
        record["scrape_meta"]["notes"].append("No /writer/ author link found in entry meta.")

    if not record["content"]["text"]:
        record["scrape_meta"]["notes"].append("Main text extraction returned empty content.")

    if piece_type == "art" and not record["derived"]["author_bio_raw"]:
        record["scrape_meta"]["notes"].append("No bio detected; art pages may have artist statements instead.")

    return record


def main():
    parser = argparse.ArgumentParser(
        description="Scrape New Orleans Review piece pages into one JSON file per piece."
    )
    parser.add_argument(
        "piece_urls_json",
        help="Path to piece_urls.json created by discover_issue_urls.py",
    )
    parser.add_argument(
        "--outdir",
        default="pieces_json",
        help="Directory for one-JSON-per-piece output",
    )
    parser.add_argument(
        "--min-delay",
        type=float,
        default=1.5,
        help="Minimum seconds between requests",
    )
    parser.add_argument(
        "--max-delay",
        type=float,
        default=3.0,
        help="Maximum seconds between requests",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-scrape and overwrite existing JSON files",
    )
    args = parser.parse_args()

    if args.max_delay < args.min_delay:
        parser.error("--max-delay must be greater than or equal to --min-delay")

    payload = json.loads(Path(args.piece_urls_json).read_text(encoding="utf-8"))
    issue_url = payload["issue_url"]
    pieces = payload["pieces"]

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)

    total = len(pieces)
    failures = []

    for idx, item in enumerate(pieces, start=1):
        piece_url = item["piece_url"]
        filename = make_output_filename_from_url(piece_url, idx)
        outfile = outdir / filename

        if outfile.exists() and not args.force:
            print(f"[{idx}/{total}] skipping existing {outfile}")
            continue

        try:
            record = scrape_piece(session, item, issue_url)
            outfile.write_text(
                json.dumps(record, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            print(f"[{idx}/{total}] wrote {outfile}")
        except Exception as exc:
            failures.append(
                {
                    "piece_url": piece_url,
                    "outfile": str(outfile),
                    "error": str(exc),
                }
            )
            print(f"[{idx}/{total}] ERROR scraping {piece_url}: {exc}", file=sys.stderr)

        if idx < total:
            time.sleep(random.uniform(args.min_delay, args.max_delay))

    if failures:
        failures_path = outdir / "_failures.json"
        failures_path.write_text(
            json.dumps(failures, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"Wrote failure log to {failures_path}")
        sys.exit(1)


if __name__ == "__main__":
    main()