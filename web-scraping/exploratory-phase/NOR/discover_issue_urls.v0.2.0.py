import argparse
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, NavigableString, Tag

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; NORExploratoryScraper/0.1; +https://example.com)",
    "Accept-Language": "en-US,en;q=0.9",
}


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def get_soup(url: str) -> BeautifulSoup:
    resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=30)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "lxml")


def find_entry_content_root(soup: BeautifulSoup) -> Tag:
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
    raise RuntimeError("Could not find issue content root")


def gather_section_links(root: Tag, base_url: str):
    rows = []
    current_section = None
    order_in_section = 0
    content_started = False

    section_names = {
        "art",
        "fiction",
        "poetry",
        "nonfiction",
        "essays",
        "essay",
        "interviews",
        "interview",
        "visual",
        "video",
        "reviews",
        "review",
    }

    for child in root.children:
        if isinstance(child, NavigableString):
            continue
        if not isinstance(child, Tag):
            continue

        name = child.name.lower()
        child_text = clean_text(child.get_text(" ", strip=True))

        # Heading-based sections: h2-h5
        if name in {"h2", "h3", "h4", "h5"} and child_text:
            current_section = child_text
            order_in_section = 0
            content_started = True
            continue

        # Bold-only paragraph/div sections like **Art** or **Poetry**
        if name in {"p", "div"}:
            direct_bold = None
            for node in child.children:
                if isinstance(node, Tag) and node.name and node.name.lower() in {"strong", "b"}:
                    direct_bold = node
                    break

            if direct_bold:
                bold_text = clean_text(direct_bold.get_text(" ", strip=True))
                if (
                    bold_text
                    and bold_text.lower() in section_names
                    and clean_text(child.get_text(" ", strip=True)) == bold_text
                ):
                    current_section = bold_text
                    order_in_section = 0
                    content_started = True
                    continue

        if not content_started or not current_section:
            continue

        if name not in {"p", "div", "ul", "ol", "blockquote"}:
            continue

        links = child.select("a[href]")
        for a in links:
            href = a.get("href", "").strip()
            if not href:
                continue

            full_url = urljoin(base_url, href)

            if not full_url.startswith("https://www.neworleansreview.org/"):
                continue

            if any(x in full_url for x in ["/writer/", "/category/", "/tag/", "/feed/", "/comments/"]):
                continue

            text = clean_text(a.get_text(" ", strip=True))
            if not text:
                continue

            order_in_section += 1
            rows.append(
                {
                    "section": current_section,
                    "order_in_section": order_in_section,
                    "piece_url": full_url,
                    "link_text_raw": text,
                }
            )

    deduped = []
    seen = set()
    for row in rows:
        key = row["piece_url"]
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)

    return deduped

# def gather_section_links(root: Tag, base_url: str):
#     rows = []
#     current_section = None
#     order_in_section = 0
#     content_started = False

#     for child in root.children:
#         if isinstance(child, NavigableString):
#             continue
#         if not isinstance(child, Tag):
#             continue

#         name = child.name.lower()
#         if name == "h3":
#             current_section = clean_text(child.get_text(" ", strip=True))
#             order_in_section = 0
#             content_started = True
#             continue

#         if not content_started or not current_section:
#             continue

#         links = child.select("a[href]") if name in {"p", "div", "ul", "ol"} else []
#         for a in links:
#             href = a.get("href", "").strip()
#             if not href:
#                 continue
#             full_url = urljoin(base_url, href)
#             if not full_url.startswith("https://www.neworleansreview.org/"):
#                 continue
#             if any(x in full_url for x in ["/writer/", "/category/", "/tag/", "/feed/", "/comments/"]):
#                 continue
#             text = clean_text(a.get_text(" ", strip=True))
#             if not text:
#                 continue
#             order_in_section += 1
#             rows.append(
#                 {
#                     "section": current_section,
#                     "order_in_section": order_in_section,
#                     "piece_url": full_url,
#                     "link_text_raw": text,
#                 }
#             )

#     deduped = []
#     seen = set()
#     for row in rows:
#         key = row["piece_url"]
#         if key in seen:
#             continue
#         seen.add(key)
#         deduped.append(row)
#     return deduped


def main():
    parser = argparse.ArgumentParser(description="Discover piece URLs from a New Orleans Review issue page.")
    parser.add_argument("issue_url", help="Issue page URL")
    parser.add_argument("--out", default="piece_urls.json", help="Output JSON path")
    parser.add_argument("--sleep", type=float, default=0.0, help="Optional pause before request")
    args = parser.parse_args()

    if args.sleep > 0:
        time.sleep(args.sleep)

    soup = get_soup(args.issue_url)

    

    root = find_entry_content_root(soup)
    title = clean_text((soup.title.get_text() if soup.title else ""))
    pieces = gather_section_links(root, args.issue_url)

    payload = {
        "journal": "New Orleans Review",
        "issue_url": args.issue_url,
        "issue_title": title,
        "piece_count": len(pieces),
        "pieces": pieces,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(pieces)} piece URLs to {out_path}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
