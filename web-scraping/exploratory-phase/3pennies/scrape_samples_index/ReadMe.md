
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
