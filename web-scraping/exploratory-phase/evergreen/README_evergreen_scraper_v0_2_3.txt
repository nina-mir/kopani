Evergreen Review scraper v0.2.3

What changed:
- Adds derived.author_bios_raw.
- If issue_json author contains commas, author_bios_raw is built by looking up a bio for each comma-separated author name.
- If issue_json author is a single name, author_bios_raw is a one-item array when a bio is found.
- Adds a generic manual_review note whenever any manual_review* note exists or when top_author_mismatch_issue_json_vs_page is present.
- Keeps existing derived.author_bio_raw for backward compatibility.

Install:
pip install requests beautifulsoup4

Single URL mode:
python scrape_evergreen_piece_v0_2_3.py   --url "http://evergreenreview.com/read/boxthorn/"   --out boxthorn.v0.2.3.json

Issue JSON mode:
python scrape_evergreen_piece_v0_2_3.py   --issue-json fw_2025_issue.json   --output-directory evergreen_fw25_pieces
