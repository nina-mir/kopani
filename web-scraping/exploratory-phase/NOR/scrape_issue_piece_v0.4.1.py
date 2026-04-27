import argparse
import hashlib
import json
import random
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup, Tag
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; NORExploratoryScraper/0.4.1; +https://example.com)",
    "Accept-Language": "en-US,en;q=0.9",
}

HEADING_TAGS = {"h1", "h2", "h3", "h4"}
TEXTISH_TAGS = {"p", "div", "blockquote", "pre", "ul", "ol", "figure", "figcaption"}
BLOCK_TEXT_TAGS = {"p", "div", "blockquote", "pre", "ul", "ol", "figcaption"}


def clean_text(text: Optional[str]) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def clean_multiline_text(text: Optional[str]) -> str:
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


def build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)
    retries = Retry(
        total=3,
        connect=3,
        read=3,
        status=3,
        backoff_factor=1.0,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def get_soup(session: requests.Session, url: str) -> BeautifulSoup:
    resp = session.get(url, timeout=30)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "lxml")


def extract_canonical(soup: BeautifulSoup, fallback_url: str) -> str:
    node = soup.select_one('link[rel="canonical"]')
    href = node.get("href", "").strip() if node else ""
    return href or fallback_url


def dedupe_author_nodes(nodes: List[Dict[str, Optional[str]]]) -> List[Dict[str, Optional[str]]]:
    seen = set()
    out = []
    for node in nodes:
        key = (node.get("display_name") or "", node.get("author_url") or "")
        if key in seen:
            continue
        seen.add(key)
        out.append(node)
    return out


def extract_header_scope(soup: BeautifulSoup) -> Optional[Tag]:
    article = soup.select_one("main article") or soup.select_one("article") or soup.select_one("main")
    if not article:
        return None
    header = article.select_one("header")
    return header or article


def extract_header(soup: BeautifulSoup) -> Dict[str, Any]:
    header_scope = extract_header_scope(soup)
    title_node = None
    meta_node = None

    if header_scope:
        title_node = header_scope.select_one("h1.entry-title") or header_scope.select_one("h1")
        meta_node = header_scope.select_one("p.entry-meta") or header_scope.select_one(".entry-meta")

    if not title_node:
        title_node = soup.select_one("main h1") or soup.select_one("article h1")
    if not meta_node:
        article = soup.select_one("main article") or soup.select_one("article")
        if article:
            meta_node = article.select_one("p.entry-meta") or article.select_one(".entry-meta")

    title_display = clean_text(title_node.get_text(" ", strip=True)) if title_node else None
    title_tag = clean_text(soup.title.get_text()) if soup.title else None

    author_nodes = []
    author_scope = meta_node or header_scope
    if author_scope:
        selectors = [
            'a[href*="/writer/"]',
            'a[rel="author"]',
        ]
        for selector in selectors:
            for a in author_scope.select(selector):
                name = clean_text(a.get_text(" ", strip=True))
                href = a.get("href", "").strip() or None
                if name:
                    author_nodes.append({"display_name": name, "author_url": href})
    author_nodes = dedupe_author_nodes(author_nodes)

    categories = []
    category_scope = meta_node or header_scope
    if category_scope:
        for a in category_scope.select('.entry-categories a[href], a[href*="/category/"]'):
            txt = clean_text(a.get_text(" ", strip=True))
            if txt and txt not in categories:
                categories.append(txt)

    return {
        "title_display": title_display,
        "title_tag": title_tag,
        "authors_raw": author_nodes,
        "categories": categories,
    }


def extract_content_node(soup: BeautifulSoup) -> Optional[Tag]:
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


def extract_main_node(soup: BeautifulSoup) -> Optional[Tag]:
    return soup.select_one("main") or extract_content_node(soup)


def extract_main_text(main_node: Optional[Tag]) -> Tuple[Optional[str], Optional[str]]:
    if not main_node:
        return None, None
    html = str(main_node)
    text = clean_multiline_text(main_node.get_text("\n", strip=False))
    return html, text


def infer_piece_type(categories: List[str], section_from_issue: Optional[str]) -> str:
    cats = " | ".join(categories).lower()
    section = (section_from_issue or "").lower()

    if "interview" in cats or "interview" in section:
        return "interview"
    if "poetry" in cats or "poetry" in section or section == "poems":
        return "poetry"
    if "essay" in cats or "nonfiction" in cats or "essay" in section or "nonfiction" in section:
        return "nonfiction"
    if "fiction" in cats or "fiction" in section:
        return "fiction"
    if "art" in cats or "art" in section:
        return "art"
    return "unknown"


def extract_breadcrumbs(soup: BeautifulSoup) -> List[str]:
    crumbs = []
    for node in soup.select(".breadcrumb [itemprop='name']"):
        txt = clean_text(node.get_text(" ", strip=True))
        if txt:
            crumbs.append(txt)
    return crumbs


def extract_json_ld(soup: BeautifulSoup) -> List[Any]:
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


def find_in_jsonld(obj: Any, key: str) -> Optional[str]:
    if isinstance(obj, dict):
        if key in obj and obj[key]:
            value = obj[key]
            if isinstance(value, str):
                return value.strip()
        for v in obj.values():
            found = find_in_jsonld(v, key)
            if found:
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = find_in_jsonld(item, key)
            if found:
                return found
    return None


def extract_publication_date(soup: BeautifulSoup, json_ld_items: List[Any]) -> Tuple[Optional[str], Optional[str]]:
    time_node = soup.select_one("time[datetime]")
    if time_node:
        return (
            time_node.get("datetime", "").strip() or None,
            clean_text(time_node.get_text(" ", strip=True)) or None,
        )

    meta_node = (
        soup.select_one('meta[property="article:published_time"]')
        or soup.select_one('meta[name="article:published_time"]')
        or soup.select_one('meta[property="og:published_time"]')
    )
    if meta_node:
        content = meta_node.get("content", "").strip() or None
        return content, None

    date_published = find_in_jsonld(json_ld_items, "datePublished")
    if date_published:
        return date_published, None

    return None, None


def direct_child_tags(node: Optional[Tag]) -> List[Tag]:
    if not node:
        return []
    return [child for child in node.children if isinstance(child, Tag)]


def child_text(child: Tag) -> str:
    if child.name and child.name.lower() in {"pre", "blockquote"}:
        return clean_multiline_text(child.get_text("\n", strip=False))
    return clean_multiline_text(child.get_text("\n", strip=True))


def looks_like_bio(text: str, authors_raw: List[Dict[str, Optional[str]]], piece_type: str) -> bool:
    txt = clean_multiline_text(text)
    if len(txt) < 40:
        return False

    lower = txt.lower()
    if lower.startswith("bio:") or lower.startswith("artist statement:"):
        return True

    author_names = [a.get("display_name", "") for a in authors_raw if a.get("display_name")]
    first_names = [name.split()[0].lower() for name in author_names if name and name.split()]
    full_names = [name.lower() for name in author_names if name]

    if any(name and lower.startswith(name) for name in full_names):
        return True
    if any(name and lower.startswith(name + " ") for name in first_names):
        return True

    bio_markers = [
        " is a writer",
        " is an artist",
        " is a poet",
        " is the author of",
        " lives in ",
        " lives and works ",
        " based in ",
        " tweets @",
        " work has appeared",
        " works have appeared",
        " recipient of",
        " earned",
        " teaches",
        " editor",
        " currently a ",
        " currently an ",
    ]
    if any(marker in lower for marker in bio_markers):
        return True

    if piece_type in {"fiction", "nonfiction", "poetry", "interview", "art"} and len(txt.split()) >= 18:
        return True

    return False


def block_text_from_tag(tag: Tag) -> Optional[str]:
    name = (tag.name or "").lower()
    if name not in BLOCK_TEXT_TAGS:
        return None

    if name == "div":
        nested_blocks = tag.find_all(list(BLOCK_TEXT_TAGS - {"div"}), recursive=True)
        if nested_blocks:
            return None

    text = child_text(tag)
    return text or None


def extract_text_after_last_hr(content_node: Optional[Tag]) -> Optional[str]:
    if not content_node:
        return None

    hrs = content_node.find_all("hr")
    if not hrs:
        return None

    last_hr = hrs[-1]
    chunks = []
    seen = set()

    for el in last_hr.next_elements:
        if el is last_hr:
            continue
        if not isinstance(el, Tag):
            continue
        if el.name == "footer":
            break
        if el is not content_node and content_node not in el.parents:
            break

        text = block_text_from_tag(el)
        if text and text not in seen:
            seen.add(text)
            chunks.append(text)

    joined = clean_multiline_text("\n\n".join(chunks))
    return joined or None


def detect_generic_bio(content_node: Optional[Tag], authors_raw: List[Dict[str, Optional[str]]], piece_type: str) -> Optional[str]:
    if not content_node:
        return None

    post_hr_text = extract_text_after_last_hr(content_node)
    if post_hr_text and looks_like_bio(post_hr_text, authors_raw, piece_type):
        return post_hr_text

    candidates = []
    for tag in content_node.find_all(["p", "div"]):
        text = clean_multiline_text(tag.get_text("\n", strip=True))
        if text:
            candidates.append(text)

    for text in reversed(candidates):
        if looks_like_bio(text, authors_raw, piece_type):
            return text

    return None


def extract_poetry_subworks(content_node: Optional[Tag], authors_raw: List[Dict[str, Optional[str]]], title_display: Optional[str]) -> Tuple[List[Dict[str, Optional[str]]], Optional[str], List[str]]:
    if not content_node:
        return [], None, []

    subworks = []
    current = None
    trailing_blocks = []
    notes = []
    started = False
    last_hr = None
    hrs = content_node.find_all("hr")
    if hrs:
        last_hr = hrs[-1]

    for child in direct_child_tags(content_node):
        if last_hr and child is last_hr:
            break

        tag = (child.name or "").lower()
        text = child_text(child)

        if tag == "hr":
            if current and clean_multiline_text(current.get("text", "")):
                current["text"] = clean_multiline_text(current["text"])
                subworks.append(current)
                current = None
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
    post_hr_text = extract_text_after_last_hr(content_node)
    if post_hr_text and looks_like_bio(post_hr_text, authors_raw, "poetry"):
        bio_candidate = post_hr_text

    if started and len(subworks) >= 2:
        notes.append("Poetry subworks segmented from inner headings and hr separators.")
    elif started and len(subworks) == 1:
        notes.append("Poetry page had inner heading structure but only one subwork block was captured.")

    if not subworks:
        body_chunks = []
        for child in direct_child_tags(content_node):
            if last_hr and child is last_hr:
                break
            tag = (child.name or "").lower()
            if tag in HEADING_TAGS:
                continue
            text = child_text(child)
            if text:
                body_chunks.append(text)

        body_text = clean_multiline_text("\n\n".join(body_chunks))
        if body_text:
            subworks.append({"title": title_display, "text": body_text})
            notes.append("Single-poem page stored as one subwork from body content.")

    if not bio_candidate and trailing_blocks:
        trailing_texts = [b["text"] for b in trailing_blocks if b.get("text")]
        joined = clean_multiline_text("\n\n".join(trailing_texts))
        if looks_like_bio(joined, authors_raw, "poetry"):
            bio_candidate = joined

    return subworks, bio_candidate, notes


def infer_issue_label(item: Dict[str, Any], categories: List[str], breadcrumbs: List[str], issue_url: str) -> Optional[str]:
    for key in ("issue_label", "issue_title"):
        value = clean_text(str(item.get(key, "")).strip()) if item.get(key) else ""
        if value:
            return value

    for crumb in breadcrumbs:
        if re.search(r"\bissue\b", crumb, re.I):
            return crumb

    for cat in categories:
        if re.search(r"\bissue\b", cat, re.I) or re.fullmatch(r"\d+", cat):
            return cat

    path = urlparse(issue_url).path.strip("/").replace("-", " ")
    path = clean_text(path)
    return path or None


def should_note_needs_ocr(content_node: Optional[Tag], piece_type: str, text_content: Optional[str]) -> bool:
    if piece_type != "poetry" or not content_node:
        return False

    text_len = len(clean_text(text_content or ""))
    img_count = len(content_node.select("img"))
    has_few_text_blocks = len(content_node.find_all(["p", "pre", "blockquote"])) <= 2

    return img_count >= 1 and (text_len < 250 or has_few_text_blocks)


def scrape_piece(session: requests.Session, item: Dict[str, Any], issue_url: str) -> Dict[str, Any]:
    url = item["piece_url"]
    section = item.get("section")
    soup = get_soup(session, url)

    canonical_url = extract_canonical(soup, url)
    header = extract_header(soup)
    main_node = extract_main_node(soup)
    content_node = extract_content_node(soup) or main_node
    content_html, text_content = extract_main_text(main_node)
    json_ld_items = extract_json_ld(soup)
    date_published_raw, date_published_display = extract_publication_date(soup, json_ld_items)
    piece_type = infer_piece_type(header["categories"], section)
    breadcrumbs = extract_breadcrumbs(soup)

    poetry_subworks = []
    poetry_bio = None
    poetry_notes = []
    if piece_type == "poetry":
        poetry_subworks, poetry_bio, poetry_notes = extract_poetry_subworks(
            content_node, header["authors_raw"], header["title_display"]
        )

    author_bio_raw = poetry_bio if poetry_bio else detect_generic_bio(content_node, header["authors_raw"], piece_type)

    record = {
        "journal": {
            "name": "New Orleans Review",
            "slug": "new-orleans-review",
        },
        "issue": {
            "issue_url": issue_url,
            "issue_label": infer_issue_label(item, header["categories"], breadcrumbs, issue_url),
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
            "date_published_raw": date_published_raw,
            "date_published_display": date_published_display,
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
            "breadcrumbs": breadcrumbs,
            "json_ld": json_ld_items,
        },
        "derived": {
            "author_bio_raw": author_bio_raw,
        },
        "scrape_meta": {
            "scraped_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "scraper_version": "0.4.1",
            "notes": poetry_notes.copy(),
        },
    }

    if not record["piece"]["title_display"]:
        record["scrape_meta"]["notes"].append("Missing visible title; fell back to title tag or null.")
    if not record["authors_raw"]:
        record["scrape_meta"]["notes"].append("No article-scoped author link found in header meta.")
    if not record["content"]["text"]:
        record["scrape_meta"]["notes"].append("Main text extraction returned empty content.")
    if piece_type == "art" and not record["derived"]["author_bio_raw"]:
        record["scrape_meta"]["notes"].append("No bio detected; art pages may have artist statements instead.")
    if piece_type == "poetry" and not record["content"]["subworks"]:
        record["scrape_meta"]["notes"].append("Poetry page did not yield structured subworks; review manually.")
    if should_note_needs_ocr(content_node, piece_type, text_content):
        record["scrape_meta"]["notes"].append("needs OCR")

    return record


def main() -> None:
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

    session = build_session()

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
        failures_path.write_text(json.dumps(failures, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Wrote failure log to {failures_path}")
        sys.exit(1)


if __name__ == "__main__":
    main()
