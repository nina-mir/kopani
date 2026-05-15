#!/usr/bin/env python3


# Run one piece:
# python scrape_evergreen_piece_v0.py \
#   --url "http://evergreenreview.com/read/boxthorn/" \
#   --out boxthorn.v0.json
# Run the first 5 pieces from the issue file:
# python scrape_evergreen_piece_v0.py \
#   --issue-json fw_2025_issue.json \
#   --limit 5 \
#   --out evergreen_sample.v0.json

import argparse
import json
import re
import time
from dataclasses import dataclass, asdict
from html import unescape
from typing import List, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; EvergreenReviewScraper/0.1)",
    "Accept-Language": "en-US,en;q=0.9",
}

CONTENT_SELECTORS = [
    ".entry-content",
    ".post-content",
    ".td-post-content",
    "article",
    ".post",
    "main",
]

BYLINE_SELECTORS = [
    ".author",
    ".entry-author",
    ".post-author",
    ".byline",
    "[rel='author']",
]

CATEGORY_SELECTORS = [
    ".cat-links a",
    ".post-categories a",
    ".entry-categories a",
    "a[rel='category tag']",
]

TAG_SELECTORS = [
    ".tags-links a",
    ".post-tags a",
    ".entry-tags a",
    "a[rel='tag']",
]


@dataclass
class PieceResult:
    source_url: str
    slug: Optional[str]
    fetch_ok: bool
    http_status: Optional[int]

    issue_label: Optional[str]
    input_title: Optional[str]
    input_author: Optional[str]
    input_type: Optional[str]

    page_title: Optional[str]
    title: Optional[str]
    title_source: Optional[str]

    author_text: Optional[str]
    authors: List[str]
    author_source: Optional[str]

    piece_type: Optional[str]
    type_source: Optional[str]

    published_date: Optional[str]
    modified_date: Optional[str]

    excerpt: Optional[str]
    dek: Optional[str]

    categories: List[str]
    tags: List[str]

    featured_image_url: Optional[str]

    word_count_approx: Optional[int]
    content_text_preview: Optional[str]
    content_html_present: bool

    notes: List[str]


def normalize_space(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    text = unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text or None


def dedupe_keep_order(items: List[str]) -> List[str]:
    seen = set()
    out = []
    for item in items:
        key = item.lower().strip()
        if key and key not in seen:
            seen.add(key)
            out.append(item.strip())
    return out


def get_slug(url: str) -> Optional[str]:
    path = urlparse(url).path.strip("/")
    if not path:
        return None
    return path.split("/")[-1]


def meta_content(soup: BeautifulSoup, *keys: str) -> Optional[str]:
    for key in keys:
        tag = soup.find("meta", attrs={"property": key}) or soup.find("meta", attrs={"name": key})
        if tag and tag.get("content"):
            val = normalize_space(tag.get("content"))
            if val:
                return val
    return None


def text_of_first(soup: BeautifulSoup, selectors: List[str]) -> Optional[str]:
    for sel in selectors:
        el = soup.select_one(sel)
        if el:
            txt = normalize_space(el.get_text(" ", strip=True))
            if txt:
                return txt
    return None


def texts_of_all(soup: BeautifulSoup, selectors: List[str]) -> List[str]:
    out = []
    for sel in selectors:
        for el in soup.select(sel):
            txt = normalize_space(el.get_text(" ", strip=True))
            if txt:
                out.append(txt)
    return dedupe_keep_order(out)


def clean_title(title: Optional[str]) -> Optional[str]:
    title = normalize_space(title)
    if not title:
        return None
    title = re.sub(r"\s*[|–—-]\s*Evergreen Review.*$", "", title, flags=re.I)
    title = re.sub(r"\s*[|–—-]\s*Evergreen.*$", "", title, flags=re.I)
    return normalize_space(title)


def split_authors(author_text: Optional[str]) -> List[str]:
    author_text = normalize_space(author_text)
    if not author_text:
        return []

    author_text = re.sub(r"^(by)\s+", "", author_text, flags=re.I)
    author_text = re.sub(r"^(written by)\s+", "", author_text, flags=re.I)

    parts = re.split(r"\s*,\s*|\s+and\s+|\s*&\s*", author_text)
    parts = [p.strip() for p in parts if p.strip()]
    return dedupe_keep_order(parts)


def infer_type(*values: Optional[str]) -> Optional[str]:
    blob = " ".join(v for v in values if v).lower()

    if re.search(r"\binterview\b|\ban interview with\b|\bq&a\b", blob):
        return "interview"
    if re.search(r"\band other poems\b|\bpoems\b|\bpoem\b", blob):
        return "poems"
    if re.search(r"\bart\b|\bportfolio\b|\bdrawings\b|\bpaintings\b|\bphotographs\b", blob):
        return "art"

    return None


def get_content_root(soup: BeautifulSoup):
    for sel in CONTENT_SELECTORS:
        el = soup.select_one(sel)
        if el:
            return el
    return soup


def build_excerpt_from_content(root) -> Optional[str]:
    paras = []
    for p in root.select("p"):
        txt = normalize_space(p.get_text(" ", strip=True))
        if txt:
            paras.append(txt)
        if len(" ".join(paras)) > 360:
            break

    if not paras:
        return None

    joined = " ".join(paras)
    if len(joined) <= 360:
        return joined
    return joined[:360].rsplit(" ", 1)[0] + "..."


def approximate_word_count(root) -> Optional[int]:
    txt = normalize_space(root.get_text(" ", strip=True))
    if not txt:
        return None
    return len(re.findall(r"\b\w+\b", txt))


def scrape_piece(url: str,
                 issue_label: Optional[str] = None,
                 input_title: Optional[str] = None,
                 input_author: Optional[str] = None,
                 input_type: Optional[str] = None,
                 timeout: int = 25) -> PieceResult:

    notes = []
    slug = get_slug(url)

    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
    except Exception as e:
        return PieceResult(
            source_url=url,
            slug=slug,
            fetch_ok=False,
            http_status=None,
            issue_label=issue_label,
            input_title=input_title,
            input_author=input_author,
            input_type=input_type,
            page_title=None,
            title=input_title,
            title_source="input" if input_title else None,
            author_text=input_author,
            authors=split_authors(input_author),
            author_source="input" if input_author else None,
            piece_type=input_type or infer_type(input_title),
            type_source="input_or_inferred",
            published_date=None,
            modified_date=None,
            excerpt=None,
            dek=None,
            categories=[],
            tags=[],
            featured_image_url=None,
            word_count_approx=None,
            content_text_preview=None,
            content_html_present=False,
            notes=[f"request_error: {e}"],
        )

    soup = BeautifulSoup(resp.text, "html.parser")
    root = get_content_root(soup)

    page_title = clean_title(soup.title.get_text(" ", strip=True) if soup.title else None)
    h1 = normalize_space(soup.h1.get_text(" ", strip=True) if soup.h1 else None)
    og_title = clean_title(meta_content(soup, "og:title", "twitter:title"))

    title = h1 or og_title or input_title or page_title
    if h1:
        title_source = "h1"
    elif og_title:
        title_source = "og:title"
    elif input_title:
        title_source = "input"
    elif page_title:
        title_source = "title_tag"
    else:
        title_source = None

    author_meta = meta_content(soup, "author", "article:author")
    byline_text = text_of_first(soup, BYLINE_SELECTORS)
    author_text = input_author or byline_text or author_meta
    if input_author:
        author_source = "input"
    elif byline_text:
        author_source = "byline"
    elif author_meta:
        author_source = "meta"
    else:
        author_source = None

    authors = split_authors(author_text)

    categories = texts_of_all(soup, CATEGORY_SELECTORS)
    tags = texts_of_all(soup, TAG_SELECTORS)

    published_date = meta_content(soup, "article:published_time", "publish_date", "pubdate", "date")
    modified_date = meta_content(soup, "article:modified_time", "lastmod")

    excerpt = meta_content(soup, "description", "og:description", "twitter:description")
    if not excerpt:
        excerpt = build_excerpt_from_content(root)
        if excerpt:
            notes.append("excerpt_from_content")

    dek = None
    if soup.h1:
        sib = soup.h1.find_next(["p", "h2", "div"])
        if sib:
            sib_text = normalize_space(sib.get_text(" ", strip=True))
            if sib_text and sib_text != excerpt and len(sib_text) <= 260:
                dek = sib_text

    featured_image_url = meta_content(soup, "og:image", "twitter:image")

    piece_type = input_type.strip() if input_type else None
    type_source = "input" if piece_type else None

    if not piece_type:
        for cat in categories:
            guess = infer_type(cat)
            if guess:
                piece_type = guess
                type_source = "category_inferred"
                break

    if not piece_type:
        guess = infer_type(title, excerpt, dek, page_title)
        if guess:
            piece_type = guess
            type_source = "title_or_excerpt_inferred"

    content_text = normalize_space(root.get_text(" ", strip=True))
    content_html_present = bool(content_text)
    word_count_approx = approximate_word_count(root)
    content_text_preview = build_excerpt_from_content(root)

    if not categories:
        notes.append("no_categories_found")
    if not tags:
        notes.append("no_tags_found")
    if not published_date:
        notes.append("no_published_date_found")
    if not authors:
        notes.append("no_authors_parsed")
    if not content_html_present:
        notes.append("no_content_text_detected")

    return PieceResult(
        source_url=url,
        slug=slug,
        fetch_ok=resp.ok,
        http_status=resp.status_code,
        issue_label=issue_label,
        input_title=input_title,
        input_author=input_author,
        input_type=input_type,
        page_title=page_title,
        title=title,
        title_source=title_source,
        author_text=author_text,
        authors=authors,
        author_source=author_source,
        piece_type=piece_type,
        type_source=type_source,
        published_date=published_date,
        modified_date=modified_date,
        excerpt=excerpt,
        dek=dek,
        categories=categories,
        tags=tags,
        featured_image_url=featured_image_url,
        word_count_approx=word_count_approx,
        content_text_preview=content_text_preview,
        content_html_present=content_html_present,
        notes=notes,
    )


def load_issue_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data, data.get("pieces") or []


def main():
    parser = argparse.ArgumentParser(description="Scrape Evergreen Review piece pages.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--url", help="Single Evergreen Review piece URL")
    group.add_argument("--issue-json", help="Path to issue JSON file")
    parser.add_argument("--limit", type=int, default=None, help="Only scrape first N pieces from issue JSON")
    parser.add_argument("--sleep", type=float, default=0.6, help="Sleep between requests")
    parser.add_argument("--out", default="evergreen_scrape_v0_output.json", help="Output JSON file")
    args = parser.parse_args()

    results = []

    if args.url:
        results.append(asdict(scrape_piece(args.url)))
    else:
        issue_data, pieces = load_issue_json(args.issue_json)
        if args.limit is not None:
            pieces = pieces[:args.limit]

        issue_label = issue_data.get("issue_label") or issue_data.get("issue_date")

        for i, piece in enumerate(pieces, start=1):
            url = piece.get("url")
            if not url:
                continue

            result = scrape_piece(
                url=url,
                issue_label=issue_label,
                input_title=piece.get("title"),
                input_author=piece.get("author"),
                input_type=piece.get("type"),
            )
            results.append(asdict(result))

            if i < len(pieces):
                time.sleep(args.sleep)

    payload = {
        "scraper_version": "evergreen_v0.1",
        "result_count": len(results),
        "results": results,
    }

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(json.dumps({
        "wrote": args.out,
        "count": len(results),
        "example_keys": list(results[0].keys()) if results else []
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()