#!/usr/bin/env python3
import argparse, json, re, time, unicodedata
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; EvergreenReviewScraper/0.2)",
    "Accept-Language": "en-US,en;q=0.9",
}

TYPE_MAP = {
    "poetry": "poems",
    "poems": "poems",
    "poem": "poems",
    "nonfiction": "nonfiction",
    "essay": "nonfiction",
    "essays": "nonfiction",
    "fiction": "fiction",
    "interview": "interview",
}


def norm(text):
    if text is None:
        return None
    text = unescape(text)
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t\f\v]+", " ", text)
    text = re.sub(r"\s*\n\s*", "\n", text)
    return text.strip() or None


def norm_space(text):
    if text is None:
        return None
    return re.sub(r"\s+", " ", unescape(text).replace("\xa0", " ")).strip() or None


def ascii_slug(text):
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def slug_from_url(url):
    p = urlparse(url).path.strip("/")
    return p.split("/")[-1] if p else None


def clean_title(text):
    text = norm_space(text)
    if not text:
        return None
    return re.sub(r"\s*[\-|–—]\s*Evergreen Review.*$", "", text, flags=re.I).strip()


def split_keywords(raw):
    if not raw:
        return []
    return [x.strip() for x in raw.split(",") if x.strip()]


def is_issue_text(text):
    t = (norm_space(text) or "").lower()
    if not t:
        return False
    return bool(re.search(r"(fall|spring|summer|winter)\s*/?\s*(fall|spring|summer|winter)?\s*20\d\d", t))


def infer_type(input_type, title, trusted_keywords):
    if input_type and input_type.strip():
        return input_type.strip().lower()
    for kw in trusted_keywords:
        k = kw.lower()
        if k in TYPE_MAP:
            return TYPE_MAP[k]
    t = (title or "").lower()
    if "and other poems" in t or " poems" in t:
        return "poems"
    if "interview" in t:
        return "interview"
    return None


def extract_visible_credits(soup):
    h1 = soup.select_one("h1.intro-title") or soup.find("h1")
    author_h3 = h1.find_next("h3") if h1 else soup.find("h3")
    author = norm_space(author_h3.get_text(" ", strip=True)) if author_h3 else None
    art_p = author_h3.find_next_sibling("p") if author_h3 else None
    if not art_p and author_h3 and author_h3.parent:
        kids = author_h3.parent.find_all("p", recursive=False)
        art_p = kids[0] if kids else None
    art_text = norm_space(art_p.get_text(" ", strip=True)) if art_p else None
    m = re.match(r"Art by\s+(.+)$", art_text or "", flags=re.I)
    visual_artist = m.group(1).strip() if m else None
    return author_h3, art_p, author, visual_artist


def parse_head_meta(soup):
    desc = None
    kw = []
    md = soup.find("meta", attrs={"name": "description"})
    if md and md.get("content"):
        desc = norm_space(md.get("content"))
    mk = soup.find("meta", attrs={"name": "keywords"})
    if mk and mk.get("content"):
        kw = split_keywords(mk.get("content"))
    return desc, kw


def head_is_trustworthy(visible_author, meta_desc, meta_keywords):
    if not visible_author:
        return False
    va = visible_author.lower()
    if meta_desc and va in meta_desc.lower():
        return True
    return any(va in k.lower() for k in meta_keywords)


def find_bio_for_name(soup, name, fallback_index=None):
    if not name:
        return None
    h4s = soup.find_all("h4")
    target = None
    lowered = name.lower().strip()
    for h4 in h4s:
        txt = norm_space(h4.get_text(" ", strip=True))
        if txt and txt.lower() == lowered:
            target = h4
            break
    if not target:
        for h4 in h4s:
            txt = norm_space(h4.get_text(" ", strip=True))
            if txt and lowered in txt.lower():
                target = h4
                break
    if not target and fallback_index is not None and len(h4s) > fallback_index:
        target = h4s[fallback_index]
    if not target:
        return None
    p = target.find_next_sibling("p")
    return norm(p.get_text("\n", strip=False)) if p else None


def extract_content(author_h3, art_p, soup):
    start = art_p or author_h3
    if not start:
        return "", ""
    blocks_html, blocks_text = [], []
    for el in start.find_all_next(["p", "blockquote", "ul", "ol", "pre", "h4", "strong"]):
        if el == art_p:
            continue
        if el.name == "h4":
            break
        if el.name == "strong" and is_issue_text(el.get_text(" ", strip=True)):
            break
        if el.name in {"p", "blockquote", "ul", "ol", "pre"}:
            txt = norm(el.get_text("\n", strip=False))
            if not txt:
                continue
            if re.match(r"^Art by\s+", norm_space(txt) or "", flags=re.I):
                continue
            if is_issue_text(txt):
                break
            blocks_html.append(str(el))
            blocks_text.append(txt)
    return "\n".join(blocks_html), "\n\n".join(blocks_text).strip()


def issue_token(issue_label, issue_number=None):
    if issue_number:
        return ascii_slug(str(issue_number))
    s = norm_space(issue_label) or "issue"
    lower = s.lower()
    seasons = []
    for season in ["spring", "summer", "fall", "winter"]:
        if season in lower:
            seasons.append(season)
    years = re.findall(r"20\d{2}", s)
    if seasons and years:
        if len(seasons) == 1:
            return f"{seasons[0]}{years[0]}"
        if len(seasons) >= 2 and len(years) >= 1:
            return f"{seasons[0]}-{seasons[1]}{years[0]}"
    return ascii_slug(s)


def last_name_token(author_name, fallback_slug):
    if not author_name:
        return fallback_slug or "unknown"
    clean = unicodedata.normalize("NFKD", author_name).encode("ascii", "ignore").decode("ascii")
    clean = re.sub(r"\s+", " ", clean).strip()
    parts = clean.split(" ")
    if not parts:
        return fallback_slug or "unknown"
    token = parts[-1].lower()
    token = re.sub(r"[^a-z0-9]+", "", token)
    return token or (fallback_slug or "unknown")


def short_slug(url, max_parts=4):
    base = slug_from_url(url) or "piece"
    parts = [p for p in base.split("-") if p]
    if not parts:
        return "piece"
    return "-".join(parts[:max_parts])


def build_piece_filename(author_name, url, issue_label, issue_number=None):
    short = short_slug(url)
    last = last_name_token(author_name, short.split("-")[-1] if short else "unknown")
    token = issue_token(issue_label, issue_number)
    return f"{last}_{short}_{token}.json"


def scrape_piece(url, issue_label=None, issue_url=None, issue_number=None, input_title=None, input_author=None, input_type=None, order_in_section=None):
    notes = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        r.raise_for_status()
    except Exception as e:
        return {
            "journal": {"name": "Evergreen Review", "slug": "evergreen-review"},
            "issue": {"issue_url": issue_url, "issue_label": issue_label, "section_from_issue": input_type or None},
            "piece": {
                "originalurl": url, "request_url": None, "source_slug": slug_from_url(url),
                "title_display": input_title, "title_tag": None, "piece_type": input_type or None,
                "categories": [], "keywords": [], "date_published_raw": None, "date_published_display": None,
                "link_text_raw": input_title, "order_in_section": order_in_section, "author": input_author,
                "visual_artist": None,
            },
            "authors_raw": [{"display_name": input_author, "author_url": None}] if input_author else [],
            "content": {"text": "", "html": "", "subworks": []},
            "page_metadata": {"canonical_url": None, "breadcrumbs": [], "meta_description": None, "meta_keywords": [], "head_metadata_trusted": False},
            "derived": {"author_bio_raw": None, "visual_artist_bio_raw": None},
            "scrape_meta": {"scraped_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "scraper_version": "0.2.0", "notes": [f"request_failed: {e}"]},
        }

    soup = BeautifulSoup(r.text, "html.parser")
    title_tag = clean_title(soup.title.get_text(" ", strip=True) if soup.title else None)
    h1 = soup.select_one("h1.intro-title") or soup.find("h1")
    title_display = norm_space(h1.get_text(" ", strip=True)) if h1 else input_title or title_tag

    canonical = None
    canon = soup.find("link", rel="canonical")
    if canon and canon.get("href"):
        canonical = canon.get("href").strip()

    author_h3, art_p, visible_author, visible_artist = extract_visible_credits(soup)
    if not visible_author and input_author:
        visible_author = input_author
        notes.append("author_taken_from_issue_json")
    if not visible_author:
        notes.append("manual_review_missing_visible_author")

    meta_desc, meta_keywords = parse_head_meta(soup)
    trusted_head = head_is_trustworthy(visible_author, meta_desc, meta_keywords)
    if (meta_desc or meta_keywords) and not trusted_head:
        notes.append("manual_review_head_metadata_untrusted")

    keywords = meta_keywords if trusted_head else []
    piece_type = infer_type(input_type, title_display, keywords)

    author_bio = find_bio_for_name(soup, visible_author, fallback_index=0)
    artist_bio = find_bio_for_name(soup, visible_artist, fallback_index=1 if visible_artist else None)
    if visible_author and not author_bio:
        notes.append("author_bio_not_found")
    if visible_artist and not artist_bio:
        notes.append("visual_artist_bio_not_found")

    content_html, content_text = extract_content(author_h3, art_p, soup)
    if not content_text:
        notes.append("content_not_found")

    breadcrumbs = [norm_space(a.get_text(" ", strip=True)) for a in soup.select(".breadcrumb a, .breadcrumbs a") if norm_space(a.get_text(" ", strip=True))]

    return {
        "journal": {"name": "Evergreen Review", "slug": "evergreen-review"},
        "issue": {
            "issue_url": issue_url,
            "issue_label": issue_label,
            "section_from_issue": input_type or None,
        },
        "piece": {
            "originalurl": url,
            "request_url": r.url,
            "source_slug": slug_from_url(url),
            "title_display": title_display,
            "title_tag": title_tag,
            "piece_type": piece_type,
            "categories": [],
            "keywords": keywords,
            "date_published_raw": None,
            "date_published_display": None,
            "link_text_raw": input_title,
            "order_in_section": order_in_section,
            "author": visible_author,
            "visual_artist": visible_artist,
        },
        "authors_raw": [{"display_name": visible_author, "author_url": None}] if visible_author else [],
        "content": {
            "text": content_text,
            "html": content_html,
            "subworks": [],
        },
        "page_metadata": {
            "canonical_url": canonical,
            "breadcrumbs": breadcrumbs,
            "meta_description": meta_desc if trusted_head else None,
            "meta_keywords": keywords,
            "head_metadata_trusted": trusted_head,
        },
        "derived": {
            "author_bio_raw": author_bio,
            "visual_artist_bio_raw": artist_bio,
        },
        "scrape_meta": {
            "scraped_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "scraper_version": "0.2.0",
            "notes": notes,
        },
    }


def load_issue_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def main():
    ap = argparse.ArgumentParser(description="Evergreen Review scraper v0.2")
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--url")
    group.add_argument("--issue-json")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--sleep", type=float, default=0.6)
    ap.add_argument("--out")
    ap.add_argument("--output-directory")
    args = ap.parse_args()

    if args.url:
        if not args.out:
            ap.error("--url requires --out")
        result = scrape_piece(args.url)
        write_json(Path(args.out), result)
        ok = bool(result.get("piece", {}).get("title_display"))
        print(f"{'SCRAPED' if ok else 'FAILED'} {args.url}")
        return

    if not args.output_directory:
        ap.error("--issue-json requires --output-directory")

    issue = load_issue_json(args.issue_json)
    pieces = issue.get("pieces") or []
    if args.limit:
        pieces = pieces[:args.limit]

    output_dir = Path(args.output_directory)
    issue_label = issue.get("issue_label") or issue.get("issue_date")
    issue_number = issue.get("issue_number")
    for i, p in enumerate(pieces, start=1):
        url = p.get("url")
        result = scrape_piece(
            url=url,
            issue_label=issue_label,
            issue_url=issue.get("issue_url"),
            issue_number=issue_number,
            input_title=p.get("title"),
            input_author=p.get("author"),
            input_type=p.get("type") or None,
            order_in_section=i,
        )
        author_name = result.get("piece", {}).get("author") or p.get("author")
        fname = build_piece_filename(author_name, url, issue_label, issue_number)
        write_json(output_dir / fname, result)
        ok = bool(result.get("piece", {}).get("title_display")) and not any(n.startswith("request_failed") for n in result.get("scrape_meta", {}).get("notes", []))
        print(f"{'SCRAPED' if ok else 'FAILED'} {url}")
        if i < len(pieces):
            time.sleep(args.sleep)


if __name__ == "__main__":
    main()
