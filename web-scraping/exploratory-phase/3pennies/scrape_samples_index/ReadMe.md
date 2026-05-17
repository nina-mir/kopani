## changelog is at the bottom of the document 

## How to run

```python
python scrape_threepenny_samples.py --out threepenny_samples_urls.json
```
The script:

- Extracts all <tr><td><a href="..."> links ending in .html

- Skips any href starting with - or ../

- Constructs full URLs as https://threepennyreview.com/samples/{filename}

- Parses issue season/year from filename pattern (_f13 → fall 2013, _su09 → summer 2009)

- Leaves title, author, section as null for later piece-level scraping


## How to run scrape_threepenny_piece.v0.py

Save the code as `scrape_threepenny_piece.py`, then run it like this:

```bash
python scrape_threepenny_piece.v0.py "https://threepennyreview.com/samples/acimansp00.html" --out acimansp00.json
```

If you want to pass issue metadata you already know:

```bash
python scrape_threepenny_piece.v0.py "https://threepennyreview.com/samples/acimansp00.html" \
  --issue-season spring \
  --issue-year 2000 \
  --out acimansp00.json
```

If you also know section or issue slug:

```bash
python scrape_threepenny_piece.v0.py "https://threepennyreview.com/samples/acimansp00.html" \
  --issue-season spring \
  --issue-year 2000 \
  --issue-slug issue-97-spring-2000 \
  --section essay \
  --out acimansp00.json
```

What it does:
- Follows the sample URL redirect to the canonical Threepenny piece page. 
- Extracts title, author, main content, and a first-pass author bio guess. 
- Writes one JSON file for that piece.

A good first test is exactly the Aciman sample you documented, since you already know what fields should appear. 


## Motivation for this specific work


## May 1, 2026
I discovered that there exists a link https://threepennyreview.com/samples/
where all the available pieces online from the earliest issues till issue 172, Winter 2023 issue inclusive that host all the URLs leading to those pieces. 
The issues 173 till current issue have a different URL which the discover_threepenny_issue_urls.py script can handle more or less. 

I want to scrape all the URLS from the /samples/ URL. There are some information that can be obtained for each piece from its url. For examples, let's have a look at this HTML tag from the samples url:

<tr><td valign="top">&nbsp;</td><td><a href="cohenandrea_f13.html">cohenandrea_f13.html</a>   </td><td align="right">2022-11-24 06:33  </td><td align="right"> 13K</td><td>&nbsp;</td></tr>

a.href is a relative url, so when scraped it should be constructed as:

"https://threepennyreview.com/samples/" + "cohenandrea_f13.html_f13.html"

The a.href text is also illuminatin -> 
issue Fall 2013
note-1: One coudl try deducing other info about the author's name but itw would be heuristic and not relaible.
note-2: Some of the URLS on the /samples/ page start with a dash. Ignore those URLS completely. 
note-3: All the URLs of interest are within "tr td a" tags. such as:

<tr><td valign="top">&nbsp;</td><td><a href="berger_su09.html">berger_su09.html</a>       </td><td align="right">2022-11-24 06:32  </td><td align="right"> 17K</td><td>&nbsp;</td></tr>

What we cannot obtain from this page: 

We cannot obtain the title of a piece, author's name, category of the piece.
More importanlty, when navigating to the piece webpage, the category is still nowhere to be found. 
I say that can be handled with a manual check. 

So, I need a scraper for https://threepennyreview.com/samples/ to scrape all the URLS after constructing them as illustrated above, then constructing the issue and that's it for now. 

## structure of the output

**Extract from each `<tr><td><a>` row:**
- Construct full URL: `https://threepennyreview.com/samples/{href}`
- Parse issue from filename pattern (e.g., `cohenandrea_f13.html` → fall 2013)
- Skip any href starting with `-` or `../`

**Output JSON with:**
- `piece_url` (full constructed URL)
- `issue_season` (parsed from `_su`/`_f`/`_wi`/`_sp`)
- `issue_year` (parsed from last 2 digits → `13` = 2013)
- Leave `title`, `author`, `section` as `null`


# Changelog - scrape_threepenny_piece.py

## v0.0.1 (2026-05-01)

### Changed
- **Improved bio detection for last non-empty paragraph**
  - Previously: script checked last paragraph as-is, including empty `<p>` tags, causing bio detection to fail on some pieces
  - Now: first filters to non-empty paragraphs, then tests the actual last content paragraph
  - Fixes issue where pieces with trailing empty `<p>` tags had `author_bio_raw: null` even when bio text was present

### Added
- **Expanded bio marker detection**
  - Added possessive author name patterns: `"{Author Name}'s"` and `"{Author Name}'s"`
  - Added publication-related markers: `"forthcoming"`, `"new book"`, `"new book of"`, `"memoir"`, `"latest book"`
  - Catches bio paragraphs like "Kim Addonizio's new book of poems... are forthcoming" that were previously missed

- **Minimum word count check for bio paragraphs**
  - Paragraphs with fewer than 3 words are not considered bio candidates
  - Prevents false positives on short fragments or navigation text

### Fixed
- Bio extraction now works correctly on pieces where:
  - The HTML has empty `<p>` tags at the end of the content container
  - The bio uses possessive author-name form rather than third-person description
  - The bio mentions forthcoming publications without using "is the author of" patterns

### Technical Details
- Modified `looks_like_bio_paragraph()` to add possessive name starts and publication markers
- Modified `split_content_and_bio()` to filter empty paragraphs before testing last paragraph
- Maintains conservative approach: only marks paragraph as bio if it matches heuristic patterns