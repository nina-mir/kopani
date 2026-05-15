Evergreen Review scraper v0.2.2

What changed:
- Uses input_author from the issue JSON as the canonical writer name when available.
- For Evergreen pages with multiple h4 tags, content now stops at the LAST h4 matching the writer name.
- Author bio extraction now uses the LAST h4 matching the writer name.
- Keeps minimal terminal output: SCRAPED <url> or FAILED <url>.

Install:
pip install requests beautifulsoup4

Single URL mode:
python scrape_evergreen_piece_v0_2_2.py   --url "http://evergreenreview.com/read/boxthorn/"   --out boxthorn.v0.2.2.json

Issue JSON mode, first 5 only:
python scrape_evergreen_piece_v0_2_2.py   --issue-json fw_2025_issue.json   --limit 5   --output-directory evergreen_fw25_pieces

Issue JSON mode, full issue:
python scrape_evergreen_piece_v0_2_2.py   --issue-json fw_2025_issue.json   --output-directory evergreen_fw25_pieces
