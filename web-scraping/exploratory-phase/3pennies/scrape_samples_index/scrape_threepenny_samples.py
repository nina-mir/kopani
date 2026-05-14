import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ThreepennyExploratoryScraper/0.1; +https://example.com)",
    "Accept-Language": "en-US,en;q=0.9",
}


def get_soup(url: str) -> BeautifulSoup:
    resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=30)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def parse_issue_from_filename(filename: str) -> dict:
    """
    Extract issue metadata from filename pattern like:
    - cohenandrea_f13.html -> fall 2013
    - berger_su09.html -> summer 2009
    - peck_w10.html -> winter 2010
    - author_sp21.html -> spring 2021
    """
    season_map = {
        "sp": "spring",
        "su": "summer",
        "f": "fall",
        "fa": "fall",
        "w": "winter",
        "wi": "winter",
    }
    
    # Pattern: _<season><2-digit-year>.html
    match = re.search(r"_(sp|su|f|fa|w|wi)(\d{2})\.html$", filename, re.IGNORECASE)
    if not match:
        return {"issue_season": None, "issue_year": None}
    
    season_code = match.group(1).lower()
    year_short = match.group(2)
    
    # Convert 2-digit year to 4-digit (00-29 = 2000s, 30-99 = 1900s)
    year_int = int(year_short)
    if year_int <= 29:
        year_full = 2000 + year_int
    else:
        year_full = 1900 + year_int
    
    return {
        "issue_season": season_map.get(season_code, season_code),
        "issue_year": year_full,
    }


def scrape_samples_index(samples_url: str) -> list[dict]:
    """
    Scrape all piece URLs from the /samples/ directory listing.
    """
    soup = get_soup(samples_url)
    pieces = []
    
    # Find all links in the page
    for a in soup.find_all("a", href=True):
        href = a.get("href", "").strip()
        
        # Skip parent directory links, dashes, or non-html files
        if not href or href.startswith("-") or href.startswith("..") or href == "/":
            continue
        
        # Only process .html files
        if not href.endswith(".html"):
            continue
        
        # Skip directories (ends with /)
        if href.endswith("/"):
            continue
        
        # Construct full URL
        piece_url = urljoin(samples_url, href)
        
        # Parse issue metadata from filename
        issue_meta = parse_issue_from_filename(href)
        
        # Only add if we successfully parsed issue info
        if issue_meta["issue_season"] and issue_meta["issue_year"]:
            pieces.append({
                "piece_url": piece_url,
                "filename": href,
                "issue_season": issue_meta["issue_season"],
                "issue_year": issue_meta["issue_year"],
                "title": None,
                "author": None,
                "section": None,
            })
    
    return pieces


def main():
    parser = argparse.ArgumentParser(
        description="Scrape all piece URLs from Threepenny Review /samples/ directory."
    )
    parser.add_argument(
        "--url",
        default="https://threepennyreview.com/samples/",
        help="Samples directory URL (default: https://threepennyreview.com/samples/)"
    )
    parser.add_argument(
        "--out",
        default="threepenny_samples_urls.json",
        help="Output JSON path"
    )
    args = parser.parse_args()
    
    pieces = scrape_samples_index(args.url)
    
    payload = {
        "journal": "The Threepenny Review",
        "source_url": args.url,
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