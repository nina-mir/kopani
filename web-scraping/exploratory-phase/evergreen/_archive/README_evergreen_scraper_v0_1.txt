Evergreen Review scraper v0.1

Install:
pip install requests beautifulsoup4

Run one piece:
python scrape_evergreen_piece_v0_1.py --url "http://evergreenreview.com/read/boxthorn/" --out boxthorn.v0.1.json

Run first 5 pieces from the issue file:
python scrape_evergreen_piece_v0_1.py --issue-json fw_2025_issue.json --limit 5 --out evergreen_sample.v0.1.json

Run the full issue:
python scrape_evergreen_piece_v0_1.py --issue-json fw_2025_issue.json --out evergreen_fw25.v0.1.json

Terminal output is intentionally minimal:
SCRAPED <url>
or
FAILED <url>
