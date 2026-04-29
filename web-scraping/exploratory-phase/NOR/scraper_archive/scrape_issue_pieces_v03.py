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
from bs4 import BeautifulSoup, NavigableString, Tag

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; NORExploratoryScraper/0.3; +https://example.com)",
    "Accept-Language": "en-US,en;q=0.9",
}

HEADING_TAGS = {"h1", "h2", "h3", "h4"}
TEXTISH_TAGS = {
    "p", "div", "blockquote", "pre", "ul", "ol", "figure", "figcaption"
}


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def clean_multiline_text(text: str) -> str:
    text = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    cleaned = []
    blank_run = 0
    for line in lines:
        if line:
            cleaned.append(line)
            blank_run = 0
        else:
            blank_run += 1
            if blank_run <= 1:
                cleaned.append("")
    return "\n".join(cleaned).strip()


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


def extract_main_node(soup: BeautifulSoup) -> Tag | None:
    return soup.select_one("main") or extract_content_node(soup)


def extract_main_text(main_node: Tag | None):
    if not main_node:
        return None, None
    html = str(main_node)
    text = clean_multiline_text(main_node.get_text("\n", strip=False))
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


def direct_child_tags(node: Tag | None):
    if not node:
        return []
    return [child for child in node.children if isinstance(child, Tag)]


def child_text(child: Tag) -> str:
    if child.name and child.name.lower() in {"pre", "blockquote"}:
        return clean_multiline_text(child.get_text("\n", strip=False))
    return clean_multiline_text(child.get_text("\n", strip=True))


def looks_like_bio(text: str, authors_raw, piece_type: str) -> bool:
    txt = clean_multiline_text(text)
    if len(txt) < 40:
        return False

    starts = txt.lower()
    if starts.startswith("bio:") or starts.startswith("artist statement:"):
        return True

    author_names = [a.get("display_name", "") for a in authors_raw if a.get("display_name")]
    first_names = [name.split()[0].lower() for name in author_names if name and name.split()]
    if any(name in starts for name in first_names):
        return True

    if piece_type in {"fiction", "nonfiction", "poetry", "interview", "art"} and len(txt.split()) >= 18:
        return True
    return False


def extract_poetry_subworks(content_node: Tag | None, authors_raw):
    if not content_node:
        return [], None, []

    subworks = []
    current = None
    trailing_blocks = []
    notes = []
    started = False

    for child in direct_child_tags(content_node):
        tag = (child.name or "").lower()
        text = child_text(child)

        if tag == "hr":
            if current and clean_multiline_text(current.get("text", "")):
                current["text"] = clean_multiline_text(current["text"])
                subworks.append(current)
                current = None
            else:
                trailing_blocks.append({"tag": "hr", "text": ""})
            continue

        if tag in HEADING_TAGS:
            if current and clean_multiline_text(current.get("text", "")):
                current["text"] = clean_multiline_text(current["text"])
                subworks.append(current)
            current = {"title": clean_text(text), "text": ""}
            started = True
            continue

        if tag in TEXTISH_TAGS or text:
            if current is not None:
                if text:
                    current["text"] += ("\n\n" if current["text"] else "") + text
            else:
                if text:
                    trailing_blocks.append({"tag": tag, "text": text})

    if current and clean_multiline_text(current.get("text", "")):
        current["text"] = clean_multiline_text(current["text"])
        subworks.append(current)

    bio_candidate = None
    trailing_texts = [b["text"] for b in trailing_blocks if b.get("text")]
    if trailing_texts:
        joined = clean_multiline_text("\n\n".join(trailing_texts))
        if looks_like_bio(joined, authors_raw, "poetry"):
            bio_candidate = joined

    if started and len(subworks) >= 2:
        notes.append("Poetry subworks segmented from inner headings and hr separators.")
    elif started and len(subworks) == 1:
        notes.append("Poetry page had inner heading structure but only one subwork block was captured.")

    return subworks, bio_candidate, notes


def detect_generic_bio(content_node: Tag | None, authors_raw, piece_type: str):
    if not content_node:
        return None
    paragraphs = [p for p in content_node.select("p") if clean_text(p.get_text(" ", strip=True))]
    if not paragraphs:
        return None
    last_text = clean_multiline_text(paragraphs[-1].get_text("\n", strip=True))
    if looks_like_bio(last_text, authors_raw, piece_type):
        return last_text
    return None


def scrape_piece(session: requests.Session, item: dict, issue_url: str):
    url = item["piece_url"]
    section = item.get("section")
    soup = get_soup(session, url)

    canonical_url = extract_canonical(soup, url)
    header = extract_header(soup)
    main_node = extract_main_node(soup)
    content_node = extract_content_node(soup) or main_node
    content_html, text_content = extract_main_text(main_node)
    piece_type = infer_piece_type(header["categories"], section)

    poetry_subworks = []
    poetry_bio = None
    poetry_notes = []
    if piece_type == "poetry":
        poetry_subworks, poetry_bio, poetry_notes = extract_poetry_subworks(content_node, header["authors_raw"])

    author_bio_raw = poetry_bio if poetry_bio else detect_generic_bio(content_node, header["authors_raw"], piece_type)

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
            "subworks": poetry_subworks,
        },
        "page_metadata": {
            "canonical_url": canonical_url,
            "breadcrumbs": extract_breadcrumbs(soup),
            "json_ld": extract_json_ld(soup),
        },
        "derived": {
            "author_bio_raw": author_bio_raw,
        },
        "scrape_meta": {
            "scraped_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "scraper_version": "0.3",
            "notes": poetry_notes.copy(),
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
    if piece_type == "poetry" and not record["content"]["subworks"]:
        record["scrape_meta"]["notes"].append("Poetry page did not yield structured subworks; review manually.")

    return record


def main():
    parser = argparse.ArgumentParser(
        description="Scrape New Orleans Review piece pages into one JSON file per piece."
    )
    parser.add_argument("piece_urls_json", help="Path to piece_urls.json created by discover_issue_urls.py")
    parser.add_argument("--outdir", default="pieces_json", help="Directory for one-JSON-per-piece output")
    parser.add_argument("--min-delay", type=float, default=1.5, help="Minimum seconds between requests")
    parser.add_argument("--max-delay", type=float, default=3.0, help="Maximum seconds between requests")
    parser.add_argument("--force", action="store_true", help="Re-scrape and overwrite existing JSON files")
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
            outfile.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"[{idx}/{total}] wrote {outfile}")
        except Exception as exc:
            failures.append({
                "piece_url": piece_url,
                "outfile": str(outfile),
                "error": str(exc),
            })
            print(f"[{idx}/{total}] ERROR scraping {piece_url}: {exc}", file=sys.stderr)

        if idx < total:
            time.sleep(random.uniform(args.min_delay, args.max_delay))

    if failures:
        failures_path = outdir / "_failures.json"
        failures_path.write_text(json.dumps(failures, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Wrote failure log to {failures_path}")
        sys.exit(1)


if __name__ == "__main__":
    main()
