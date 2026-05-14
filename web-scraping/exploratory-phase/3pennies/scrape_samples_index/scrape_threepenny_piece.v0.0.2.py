# Use it like this:
# 
# python scrape_threepenny_piece.v0.0.2.py --input-json small_sample_pieces.json --out-dir threepenny_outputs
#
# That will write files like aciman_sp00.json, addonizio_f15.json, etc., into threepenny_outputs/. 
# It uses each record’s filename field to name the output file.
#
# Single-piece mode still works too:
# python scrape_threepenny_piece.v0.0.2.py "https://threepennyreview.com/samples/aciman_sp00.html" --out aciman_sp00.json
# 
# You can also test a smaller run with:
# python scrape_threepenny_piece.v0.0.2.py --input-json small_sample_pieces.json --out-dir threepenny_outputs --limit 3
#
#  And add pacing if you want:
# python scrape_threepenny_piece.v0.0.2.py --input-json small_sample_pieces.json --out-dir threepenny_outputs --sleep 1

import argparse
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup, Tag


DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ThreepennyExploratoryScraper/0.1; +https://example.com)",
    "Accept-Language": "en-US,en;q=0.9",
}


def clean_text(text: str) -> str:
    text = text or ""
    text = text.replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()


def clean_multiline_text(text: str) -> str:
    text = text or ""
    text = text.replace("\r", "\n").replace("\xa0", " ")
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    return "\n".join(lines).strip()


def slug_from_url(url: str) -> str | None:
    path = urlparse(url).path.strip("/")
    if not path:
        return None
    return path.split("/")[-1]


def output_stem_from_record(record: dict) -> str:
    filename = clean_text(record.get("filename"))
    if filename:
        return Path(filename).stem

    piece_url = clean_text(record.get("piece_url"))
    if piece_url:
        path_name = Path(urlparse(piece_url).path).name
        if path_name:
            return Path(path_name).stem

    return "threepenny_piece"


def get_response_and_soup(url: str):
    resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=30, allow_redirects=True)
    resp.raise_for_status()
    return resp, BeautifulSoup(resp.text, "lxml")


def extract_title(soup: BeautifulSoup) -> str | None:
    og = soup.find("meta", attrs={"property": "og:title"})
    if og and og.get("content"):
        title = clean_text(og.get("content"))
        title = re.sub(r"\s+[–-]\s+The Threepenny Review$", "", title, flags=re.I)
        if title:
            return title

    title_tag = soup.find("title")
    if title_tag:
        title = clean_text(title_tag.get_text(" ", strip=True))
        title = re.sub(r"\s+[–-]\s+The Threepenny Review$", "", title, flags=re.I)
        if title:
            return title

    h1 = soup.find("h1")
    if h1:
        title = clean_text(h1.get_text(" ", strip=True))
        if title:
            return title

    return None


def extract_author(soup: BeautifulSoup) -> str | None:
    excerpt_widget = soup.select_one(".elementor-widget-theme-post-excerpt .elementor-widget-container")
    if excerpt_widget:
        author = clean_text(excerpt_widget.get_text(" ", strip=True))
        return author or None

    return None


def get_post_content_container(soup: BeautifulSoup) -> Tag | None:
    container = soup.select_one(".elementor-widget-theme-post-content .elementor-widget-container")
    if container:
        return container

    article = soup.find("article")
    if article:
        return article

    main = soup.find("main")
    if main:
        return main

    return None


def extract_paragraphs(content_container: Tag) -> list[str]:
    paragraphs = []

    for p in content_container.find_all("p"):
        text = p.get_text("\n", strip=True)
        text = clean_multiline_text(text)
        if not text:
            continue
        paragraphs.append(text)

    return paragraphs


def looks_like_bio_paragraph(text: str, author_name: str | None) -> bool:
    if not text:
        return False

    cleaned = clean_text(text)
    if len(cleaned.split()) < 3:
        return False

    low = cleaned.lower()

    if author_name:
        author_clean = clean_text(author_name)
        author_low = author_clean.lower()

        full_name_starts = [
            author_low + " ",
            author_low + ",",
            author_low + ":",
            author_low + ";",
            author_low + "'s ",
            author_low + "’s ",
            author_low + " is ",
            author_low + " has ",
            author_low + " was ",
            author_low + " whose ",
        ]
        if any(low.startswith(prefix) for prefix in full_name_starts):
            return True

    bio_markers = [
        " is the author of ",
        " is author of ",
        " teaches ",
        " teaches at ",
        " lives in ",
        " lives with ",
        " lives and works ",
        " has published ",
        " has written ",
        " has received ",
        " has won ",
        " work has appeared in ",
        " work appears in ",
        " is a writer ",
        " is a poet ",
        " is an essayist ",
        " is a novelist ",
        " is a professor ",
        " forthcoming",
        " forthcoming.",
        " new book ",
        " new book of ",
        " memoir ",
        " latest book ",
        " lifetime achievement ",
        " award ",
        " awards ",
        " whose published books ",
    ]

    if any(marker in low for marker in bio_markers):
        return True

    if author_name:
        author_clean = clean_text(author_name)
        author_low = author_clean.lower()

        last_name = author_low.split()[-1]
        if len(last_name) >= 4 and low.startswith(last_name + " "):
            return True
        if len(last_name) >= 4 and low.startswith(last_name + ","):
            return True
        if len(last_name) >= 4 and low.startswith(last_name + "'s "):
            return True
        if len(last_name) >= 4 and low.startswith(last_name + "’s "):
            return True

    return False


def split_content_and_bio(paragraphs: list[str], author_name: str | None) -> tuple[str | None, str | None, list[str]]:
    if not paragraphs:
        return None, None, []

    trimmed = [p for p in paragraphs if clean_text(p)]

    if not trimmed:
        return None, None, []

    bio_paragraphs = []
    content_paragraphs = trimmed

    last_para = trimmed[-1]

    if looks_like_bio_paragraph(last_para, author_name):
        bio_paragraphs = [last_para]
        content_paragraphs = trimmed[:-1]

        if content_paragraphs:
            prev_para = content_paragraphs[-1]
            if looks_like_bio_paragraph(prev_para, author_name):
                bio_paragraphs.insert(0, prev_para)
                content_paragraphs = content_paragraphs[:-1]

    content_text = "\n\n".join(content_paragraphs).strip() or None
    bio_text = "\n\n".join(bio_paragraphs).strip() or None

    return content_text, bio_text, trimmed


def scrape_threepenny_piece(piece_url: str, source_issue_meta: dict | None = None) -> dict:
    resp, soup = get_response_and_soup(piece_url)

    final_url = resp.url
    canonical_link = soup.find("link", rel="canonical")
    canonical_url = canonical_link.get("href", "").strip() if canonical_link and canonical_link.get("href") else final_url

    title = extract_title(soup)
    author = extract_author(soup)

    content_container = get_post_content_container(soup)
    raw_paragraphs = extract_paragraphs(content_container) if content_container else []

    content_text, author_bio_raw, raw_paragraphs_full = split_content_and_bio(raw_paragraphs, author)

    issue_meta = source_issue_meta or {}

    return {
        "journal": "The Threepenny Review",
        "piece_url": piece_url,
        "final_url": final_url,
        "canonical_url": canonical_url,
        "slug": slug_from_url(canonical_url),
        "title": title,
        "author": author,
        "section": issue_meta.get("section"),
        "issue_season": issue_meta.get("issue_season"),
        "issue_year": issue_meta.get("issue_year"),
        "issue_number": issue_meta.get("issue_number"),
        "issue_slug": issue_meta.get("issue_slug"),
        "content": {
            "text": content_text,
            "raw_paragraphs": raw_paragraphs_full,
        },
        "derived": {
            "author_bio_raw": author_bio_raw,
        },
    }


def scrape_from_record(record: dict) -> dict:
    piece_url = clean_text(record.get("piece_url"))
    if not piece_url:
        raise ValueError("Record missing piece_url")

    source_issue_meta = {
        "issue_season": record.get("issue_season"),
        "issue_year": record.get("issue_year"),
        "issue_number": record.get("issue_number"),
        "issue_slug": record.get("issue_slug"),
        "section": record.get("section"),
    }

    data = scrape_threepenny_piece(piece_url, source_issue_meta=source_issue_meta)
    data["source_filename"] = record.get("filename")
    return data


def run_batch(input_json_path: str, out_dir: str, sleep_seconds: float = 0.0, limit: int | None = None):
    in_path = Path(input_json_path)
    records = json.loads(in_path.read_text(encoding="utf-8"))
    if not isinstance(records, list):
        raise ValueError("Input JSON must be a list of piece records")

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    written = 0
    for idx, record in enumerate(records):
        if limit is not None and written >= limit:
            break

        if sleep_seconds > 0 and written > 0:
            time.sleep(sleep_seconds)

        data = scrape_from_record(record)
        stem = output_stem_from_record(record)
        file_path = out_path / f"{stem}.json"
        file_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        written += 1
        print(f"[{written}] Wrote {file_path}")

    print(f"Done. Wrote {written} piece files to {out_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Scrape Threepenny Review piece pages, singly or from a JSON list."
    )
    parser.add_argument("piece_url", nargs="?", help="Single piece URL, often from /samples/")
    parser.add_argument("--out", default="threepenny_piece.json", help="Output JSON path for single-piece mode")
    parser.add_argument("--sleep", type=float, default=0.0, help="Optional pause before requests")
    parser.add_argument("--issue-season", default=None)
    parser.add_argument("--issue-year", type=int, default=None)
    parser.add_argument("--issue-number", type=int, default=None)
    parser.add_argument("--issue-slug", default=None)
    parser.add_argument("--section", default=None)
    parser.add_argument("--input-json", default=None, help="Path to a JSON file containing a list of piece records")
    parser.add_argument("--out-dir", default="threepenny_piece_outputs", help="Output directory for batch mode")
    parser.add_argument("--limit", type=int, default=None, help="Optional limit for batch mode")
    args = parser.parse_args()

    if args.input_json:
        run_batch(args.input_json, args.out_dir, sleep_seconds=args.sleep, limit=args.limit)
        return

    if not args.piece_url:
        parser.error("Provide piece_url for single mode, or use --input-json for batch mode")

    if args.sleep > 0:
        time.sleep(args.sleep)

    source_issue_meta = {
        "issue_season": args.issue_season,
        "issue_year": args.issue_year,
        "issue_number": args.issue_number,
        "issue_slug": args.issue_slug,
        "section": args.section,
    }

    data = scrape_threepenny_piece(args.piece_url, source_issue_meta=source_issue_meta)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote piece data to {out_path}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
