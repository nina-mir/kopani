Evergreen Review scraper v0.2.1

What changed:
- Content extraction now stops only when an h4 matches the writer's name.
- Generic h4 tags inside the body no longer end content capture.
- Added normalized per-block deduping in content extraction.
- Version bumped from 0.2.0 to 0.2.1.

Install:
pip install requests beautifulsoup4

Single URL mode:
python scrape_evergreen_piece_v0_2_1.py   --url "http://evergreenreview.com/read/boxthorn/"   --out boxthorn.v0.2.1.json

Issue JSON mode, first 5 only:
python scrape_evergreen_piece_v0_2_1.py   --issue-json fw_2025_issue.json   --limit 5   --output-directory evergreen_fw25_pieces

Issue JSON mode, full issue:
python scrape_evergreen_piece_v0_2_1.py   --issue-json fw_2025_issue.json   --output-directory evergreen_fw25_pieces

Terminal output:
SCRAPED <url>
or
FAILED <url>
