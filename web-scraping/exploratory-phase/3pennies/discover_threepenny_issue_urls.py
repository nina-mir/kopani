import argparse
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup, Tag


DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ThreepennyExploratoryScraper/0.1; +https://example.com)",
    "Accept-Language": "en-US,en;q=0.9",
}


JUNK_PHRASES = {
    "table talk",
    "thanks to our donors",
    "back to top of page",
    "order this issue",
    "please click here",
}


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def get_soup(url: str) -> BeautifulSoup:
    resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=30)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "lxml")


def issue_slug_from_url(issue_url: str) -> str | None:
    path = urlparse(issue_url).path.strip("/")
    return path or None


def parse_issue_meta(issue_url: str, soup: BeautifulSoup) -> dict:
    """
    Prefer parsing issue metadata from the <title> element, e.g.:
    <title>Issue 144, Winter 2016 – The Threepenny Review</title>

    Fallback to parsing the URL slug, e.g.:
    /issue-180-winter-2025/
    """
    default = {
        "issue_slug": issue_slug_from_url(issue_url),
        "issue_number": None,
        "issue_season": None,
        "issue_year": None,
    }

    title_tag = soup.find("title")
    title_text = clean_text(title_tag.get_text(" ", strip=True)) if title_tag else ""

    # Example:
    # "Issue 144, Winter 2016 – The Threepenny Review"
    # "Issue 142, Summer 2015 - The Threepenny Review"
    title_match = re.search(
        r"Issue\s+(\d+)\s*,\s*(Spring|Summer|Fall|Winter)\s+(\d{4})\b",
        title_text,
        flags=re.IGNORECASE,
    )
    if title_match:
        issue_number = int(title_match.group(1))
        issue_season = title_match.group(2).lower()
        issue_year = int(title_match.group(3))
        return {
            "issue_slug": f"issue-{issue_number}-{issue_season}-{issue_year}",
            "issue_number": issue_number,
            "issue_season": issue_season,
            "issue_year": issue_year,
        }

    # Fallback to current Threepenny URL style:
    # /issue-180-winter-2025/
    url_match = re.search(
        r"/issue-(\d+)-(spring|summer|fall|winter)-(\d{4})/?$",
        issue_url,
        flags=re.IGNORECASE,
    )
    if url_match:
        issue_number = int(url_match.group(1))
        issue_season = url_match.group(2).lower()
        issue_year = int(url_match.group(3))
        return {
            "issue_slug": f"issue-{issue_number}-{issue_season}-{issue_year}",
            "issue_number": issue_number,
            "issue_season": issue_season,
            "issue_year": issue_year,
        }

    return default


def find_toc_div(soup: BeautifulSoup) -> Tag:
    toc_string = soup.find(string=lambda s: s and "Table of Contents" in s)
    if not toc_string:
        raise RuntimeError("Could not find 'Table of Contents' marker")

    toc_tag = toc_string.parent
    toc_div = toc_tag.find_next("div")
    if not toc_div:
        raise RuntimeError("Could not find TOC div after 'Table of Contents' marker")

    return toc_div


def split_lines_from_p(p: Tag) -> list[str]:
    html = str(p)
    html = re.sub(r"<br\s*/?>", "\n", html, flags=re.I)
    temp = BeautifulSoup(html, "lxml")
    text = temp.get_text("\n", strip=True)
    lines = [clean_text(x) for x in text.split("\n")]
    return [x for x in lines if x]


def split_type_and_title(text: str):
    m = re.match(r"^\s*([^:]{2,40})\s*:\s*(.+?)\s*$", text)
    if not m:
        return None, text
    return clean_text(m.group(1)), clean_text(m.group(2))


def looks_like_open_piece_link(url: str) -> bool:
    if not url:
        return False
    if "threepennyreview.com" not in url:
        return False
    bad = ["/order", "/donate", "/cart", "/shop", "#top", "tocs/"]
    return not any(x in url.lower() for x in bad)


def parse_toc_entries(toc_div: Tag, issue_url: str):
    rows = []
    seen = set()
    order = 0

    for p in toc_div.find_all("p", recursive=False):
        p_text = clean_text(p.get_text(" ", strip=True)).lower()
        if not p_text or p_text in JUNK_PHRASES:
            continue

        links = p.find_all("a", href=True)
        open_links = []
        for a in links:
            full_url = urljoin(issue_url, a.get("href", "").strip())
            if looks_like_open_piece_link(full_url):
                open_links.append((a, full_url))

        if not open_links:
            continue

        lines = split_lines_from_p(p)
        if not lines:
            continue

        author_raw = lines[0]
        if clean_text(author_raw).lower() in JUNK_PHRASES:
            author_raw = None

        title_line = None
        for line in lines[1:]:
            low = line.lower()
            if low in JUNK_PHRASES:
                continue
            if ":" in line or len(lines) == 1:
                title_line = line
                break

        if not title_line:
            title_line = clean_text(open_links[0][0].get_text(" ", strip=True))

        section, title_from_issue = split_type_and_title(title_line)

        for a, full_url in open_links:
            if full_url in seen:
                continue
            seen.add(full_url)
            order += 1
            rows.append(
                {
                    "section": section,
                    "order_in_issue": order,
                    "piece_url": full_url,
                    "link_text_raw": clean_text(a.get_text(" ", strip=True)),
                    "title_from_issue": title_from_issue,
                    "author_from_issue_raw": author_raw,
                }
            )

    return rows


def main():
    parser = argparse.ArgumentParser(
        description="Discover open piece URLs from a Threepenny Review issue page."
    )
    parser.add_argument("issue_url", help="Issue page URL")
    parser.add_argument("--out", default="threepenny_piece_urls.json", help="Output JSON path")
    parser.add_argument("--sleep", type=float, default=0.0, help="Optional pause before request")
    args = parser.parse_args()

    if args.sleep > 0:
        time.sleep(args.sleep)

    soup = get_soup(args.issue_url)
    issue_meta = parse_issue_meta(args.issue_url, soup)
    toc_div = find_toc_div(soup)
    pieces = parse_toc_entries(toc_div, args.issue_url)

    payload = {
        "journal": "The Threepenny Review",
        "issue_url": args.issue_url,
        "issue_slug": issue_meta["issue_slug"],
        "issue_number": issue_meta["issue_number"],
        "issue_season": issue_meta["issue_season"],
        "issue_year": issue_meta["issue_year"],
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