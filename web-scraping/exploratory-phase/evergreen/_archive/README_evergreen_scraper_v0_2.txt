Evergreen Review scraper v0.2

What changed:
- When you use --issue-json, the scraper writes one JSON file per piece.
- Filenames follow:
  <writer-last-name>_<short-slug>_<issue-token>.json
- Supports --limit and --output-directory.
- Terminal output stays minimal: SCRAPED <url> or FAILED <url>

Install:
pip install requests beautifulsoup4

Single URL mode:
python scrape_evergreen_piece_v0_2.py \
  --url "http://evergreenreview.com/read/boxthorn/" \
  --out boxthorn.v0.2.json

Issue JSON mode, first 5 only:
python scrape_evergreen_piece_v0_2.py \
  --issue-json fw_2025_issue.json \
  --limit 5 \
  --output-directory evergreen_fw25_pieces

Issue JSON mode, full issue:
python scrape_evergreen_piece_v0_2.py \
  --issue-json fw_2025_issue.json \
  --output-directory evergreen_fw25_pieces

Filename examples:
- wayne_more-than-anything-africa-wayne_fall-winter2025.json
- fernandez_silent-upon-a-peak_fall-winter2025.json

Notes:
- The short slug is derived from the first few parts of the URL slug.
- The issue token comes from issue_number when present; otherwise it is derived from issue_label / issue_date.
