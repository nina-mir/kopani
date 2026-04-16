# New Orleans Review exploratory scraper

This folder contains two small Python scripts:

- `discover_issue_urls.py` — fetches the issue page and writes a JSON manifest of piece URLs.
- `scrape_issue_pieces.py` — reads that manifest and writes one JSON file per piece URL.

## What it captures

For each piece page, the scraper writes a JSON file with:

- original URL and canonical URL
- issue URL, issue label, and issue section
- display title and HTML `<title>` text
- raw author names and `/writer/` profile URLs
- inferred piece type from category tags and issue section
- the entirety of the page's `<main>` text in `content.text`
- the raw HTML for the page's `<main>` block in `content.html`
- JSON-LD, breadcrumbs, and a best-effort author bio field

## 1) Create a virtual environment

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 2) Discover all piece URLs for the issue

```bash
python discover_issue_urls.py "https://www.neworleansreview.org/issue-53-summer-2025/" --out piece_urls.json
```

That creates `piece_urls.json` with issue metadata plus a `pieces` array.

## 3) Scrape every piece into one JSON file per piece

```bash
python scrape_issue_pieces.py piece_urls.json --outdir pieces_json
```

By default, the scraper sleeps 1.5 to 3.0 seconds between piece requests.

You can make it slower:

```bash
python scrape_issue_pieces.py piece_urls.json --outdir pieces_json --min-delay 2.0 --max-delay 4.0
```

## Output layout

```text
nor_scraper/
  discover_issue_urls.py
  scrape_issue_pieces.py
  requirements.txt
  README.md
  piece_urls.json
  pieces_json/
    inheritance.json
    throat-fish.json
    cetacean-stranding.json
    ...
```

## Notes

- This is an exploratory scraper, not a final normalized ingestion pipeline.
- Poetry pages with multiple poems under one URL stay as one JSON file; inner poem titles are captured in `content.subworks` when detected.
- The scraper preserves the full text of the `<main>` tag in `content.text`, which may include the author bio or artist statement when they appear inside `<main>`.
- `derived.author_bio_raw` is best-effort and should be reviewed manually.
