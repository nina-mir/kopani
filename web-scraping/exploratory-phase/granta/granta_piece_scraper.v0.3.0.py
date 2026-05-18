#!/usr/bin/env python3
"""
Granta piece scraper.

Usage:
  # Single URL:
  python granta_piece_scraper.py --url https://granta.com/the-chinese-psyche/

  # Specific issue from JSON:
  python granta_piece_scraper.py --issue-json granta_issues.json --issue-number 174

  # All issues in JSON:
  python granta_piece_scraper.py --issue-json granta_issues.json --all

  # Override output directory:
  python granta_piece_scraper.py --issue-json granta_issues.json --issue-number 174 --out-dir ./output

Output: granta_pieces/{issue-number}-{slug}/{piece-slug}.json
"""

import re
import json
import subprocess
import time
import os
import sys
import argparse
import urllib.request
import urllib.error
from datetime import datetime, timezone

SCRAPER_VERSION = "0.3.0"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

# Tags whose entire subtree (opening tag, children, closing tag) should be removed
# from content.html — these never contain article prose
STRIP_ELEMENTS = {
    'script', 'style', 'noscript', 'iframe', 'svg', 'path', 'g', 'defs',
    'clippath', 'rect', 'circle', 'polygon', 'polyline', 'ellipse', 'line',
    'symbol', 'use', 'filter', 'mask', 'pattern', 'marker', 'image',
    'input', 'button', 'form', 'select', 'option', 'textarea',
    'meta', 'link', 'base',
}

# ─── Utilities ────────────────────────────────────────────────────────────────

def fetch(url):
    """Fetch a URL using Python's urllib — cross-platform, no subprocess,
    no Windows curl/PowerShell alias issues. Follows redirects automatically.
    Always ensures a trailing slash to avoid redirect chains on WordPress sites.
    """
    # Normalise: ensure trailing slash (WordPress always redirects to it anyway)
    if '?' not in url and not url.endswith('/'):
        url = url + '/'

    req = urllib.request.Request(
        url,
        headers={
            'User-Agent': UA,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'identity',   # avoid gzip so we get plain bytes
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
            # Detect encoding from Content-Type header, default to utf-8
            ct = resp.headers.get_content_charset() or 'utf-8'
            return raw.decode(ct, errors='replace')
    except urllib.error.URLError as e:
        raise RuntimeError(f"fetch failed for {url}: {e}") from e


def strip_tags(html):
    """Remove all HTML tags, return plain text."""
    return re.sub(r'<[^>]+>', '', html)


def clean_text(text):
    """Strip tags, decode common HTML entities, collapse whitespace."""
    text = strip_tags(text)
    replacements = [
        ('&amp;', '&'), ('&nbsp;', ' '), ('&#038;', '&'), ('&quot;', '"'),
        ('&lt;', '<'), ('&gt;', '>'), ('&#8217;', '\u2019'), ('&#8216;', '\u2018'),
        ('&#8220;', '\u201c'), ('&#8221;', '\u201d'), ('&#8230;', '\u2026'),
        ('&#8211;', '\u2013'), ('&#8212;', '\u2014'), ('&#160;', ' '),
    ]
    for src, dst in replacements:
        text = text.replace(src, dst)
    return ' '.join(text.split()).strip()


def remove_element(html, tag):
    """
    Remove all occurrences of <tag ...>...</tag> (and self-closing <tag ... />)
    from html, including any nested content.
    Uses a simple stack-based approach to handle nesting correctly.
    """
    tag_lower = tag.lower()
    result = []
    i = 0
    depth = 0

    while i < len(html):
        # Check for opening tag
        open_match = re.match(
            rf'<{tag_lower}(?:\s[^>]*)?>',
            html[i:], re.IGNORECASE
        )
        # Check for self-closing tag
        self_close = re.match(
            rf'<{tag_lower}(?:\s[^>]*)?\s*/>',
            html[i:], re.IGNORECASE
        )
        # Check for closing tag
        close_match = re.match(
            rf'</{tag_lower}\s*>',
            html[i:], re.IGNORECASE
        )

        if self_close and depth == 0:
            i += len(self_close.group(0))
        elif open_match:
            depth += 1
            i += len(open_match.group(0))
        elif close_match:
            if depth > 0:
                depth -= 1
                i += len(close_match.group(0))
            else:
                # Stray closing tag — skip it
                i += len(close_match.group(0))
        else:
            if depth == 0:
                result.append(html[i])
            i += 1

    return ''.join(result)


def clean_html(raw_html):
    """
    Remove all non-prose elements from article HTML.
    Keeps: p, h1-h6, em, strong, a, ul, ol, li, br, blockquote, hr, div, span
    Strips entire subtrees of: script, style, svg, path, iframe, form, input, etc.
    Also strips HTML comments and collapses excess whitespace.
    """
    html = raw_html

    # 1. Remove entire element subtrees for non-text tags
    for tag in STRIP_ELEMENTS:
        html = remove_element(html, tag)

    # 2. Remove HTML comments
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)

    # 3. Remove empty divs/spans (no text content after stripping)
    #    Repeat a few times to catch nested empties
    for _ in range(4):
        html = re.sub(r'<(div|span)[^>]*>\s*</\1>', '', html)

    # 4. Remove ad/sidebar wrapper divs by class patterns
    for class_pattern in [
        r'd-lg-none', r'd-block d-md-none', r'widget__article-sidebar',
        r'article-sidebar', r'litbreaker', r'hidden-xs',
    ]:
        html = re.sub(
            rf'<div[^>]*class="[^"]*{re.escape(class_pattern)}[^"]*"[^>]*>.*?</div>',
            '', html, flags=re.DOTALL
        )

    # 5. Decode entities
    html = (html
        .replace('&amp;', '&').replace('&nbsp;', ' ').replace('&#038;', '&')
        .replace('&quot;', '"').replace('&lt;', '<').replace('&gt;', '>')
        .replace('&#8217;', '\u2019').replace('&#8216;', '\u2018')
        .replace('&#8220;', '\u201c').replace('&#8221;', '\u201d')
        .replace('&#8230;', '\u2026').replace('&#8211;', '\u2013')
        .replace('&#8212;', '\u2014').replace('&#160;', ' ')
    )

    # 6. Collapse whitespace runs inside tags and between tags
    html = re.sub(r'\n\s*\n\s*\n+', '\n\n', html)
    html = re.sub(r'[ \t]+', ' ', html)

    return html.strip()


def slug_from_url(url):
    return url.rstrip('/').split('/')[-1]


def author_surname(display_name):
    """Extract lowercase last word of an author name for use in filenames."""
    if not display_name:
        return ''
    # Handle 'Last, First' format
    if ',' in display_name:
        return re.sub(r'[^a-z0-9]', '', display_name.split(',')[0].strip().lower())
    parts = display_name.strip().split()
    return re.sub(r'[^a-z0-9]', '', parts[-1].lower()) if parts else ''


def piece_filename(slug, author_name):
    """Build output filename: slug--surname.json
    Appending surname disambiguates pieces with identical titles/slugs.
    """
    surname = author_surname(author_name)
    if surname and surname not in slug:
        return f"{slug}--{surname}"
    return slug


def now_utc():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def issue_dir_name(issue_number, issue_label):
    """Generate a directory name like '174-therapy' from issue metadata."""
    if issue_number:
        # Extract slug from label, e.g. "Granta 174: Therapy" → "therapy"
        label_slug = re.sub(r'^[Gg]ranta\s+\d+[:\s]*', '', issue_label or '')
        label_slug = re.sub(r'[^a-zA-Z0-9\s-]', '', label_slug).strip().lower()
        label_slug = re.sub(r'\s+', '-', label_slug)[:40].rstrip('-')
        if label_slug:
            return f"{issue_number}-{label_slug}"
        return str(issue_number)
    # Seasonal fallback
    if issue_label:
        s = re.sub(r'[^a-zA-Z0-9\s-]', '', issue_label).lower()
        return re.sub(r'\s+', '-', s)[:50].rstrip('-')
    return "unknown-issue"


# ─── Core Parser ──────────────────────────────────────────────────────────────

def parse_piece(url, html, issue_context=None):
    """
    Parse a Granta piece page into the target schema.
    issue_context: dict with keys issue_url, issue_label, issue_number,
                   issue_date, type, edition
    """
    notes = []
    url = url.rstrip('/')

    # ── Title ─────────────────────────────────────────────────────────────────
    og_title_m = re.search(r'<meta property="og:title" content="([^"]+)"', html)
    if og_title_m:
        t = clean_text(og_title_m.group(1))
        title_display = re.sub(r'\s*\|.*$', '', t).strip()
        title_tag = clean_text(og_title_m.group(1))
    else:
        h1_m = re.search(
            r'class="[^"]*article-twenty-twenty-style-title[^"]*"[^>]*>\s*(.*?)\s*</h1>',
            html, re.DOTALL
        )
        title_display = clean_text(h1_m.group(1)) if h1_m else ""
        title_tag = title_display
        if not title_display:
            notes.append("manual_review: title not found")

    # ── Canonical URL ─────────────────────────────────────────────────────────
    canon_m = re.search(r'<link rel="canonical" href="([^"]+)"', html)
    canonical = canon_m.group(1).rstrip('/') if canon_m else url

    # ── Date ──────────────────────────────────────────────────────────────────
    date_m = re.search(r'"datePublished":"([^"]+)"', html)
    date_raw = date_m.group(1) if date_m else None
    date_display = date_raw[:10] if date_raw else None

    # ── Content type ──────────────────────────────────────────────────────────
    piece_type = (issue_context or {}).get('type')
    if not piece_type:
        section_m = re.search(r'"articleSection":\["([^"]+)"\]', html)
        if section_m:
            piece_type = clean_text(section_m.group(1))

    # ── Keywords ──────────────────────────────────────────────────────────────
    kw_m = re.search(r'"keywords":\[(.*?)\]', html, re.DOTALL)
    keywords = (
        [k.strip().strip('"') for k in kw_m.group(1).split(',') if k.strip().strip('"')]
        if kw_m else []
    )

    # ── Meta description ──────────────────────────────────────────────────────
    desc_m = (
        re.search(r'<meta name="description" content="([^"]+)"', html) or
        re.search(r'<meta property="og:description" content="([^"]+)"', html)
    )
    meta_desc = clean_text(desc_m.group(1)) if desc_m else None

    # ── Edition ───────────────────────────────────────────────────────────────
    edition = (issue_context or {}).get('edition')
    if not edition:
        edition = 'Online Edition' if 'The Online Edition' in html else 'Print'

    # ── Contributors (authors + translators) ─────────────────────────────────
    # Each contributor block pattern:
    #   <h1 class="article-contributor-section_title">NAME</h1>
    #   <p class="article-contributor-section_content">BIO TEXT</p>
    #   <a class="article-contributor-section_link" href="URL">...
    contrib_blocks = list(re.finditer(
        r'class="article-contributor-section_title">(.*?)</h1>.*?'
        r'class="article-contributor-section_content">(.*?)</p>.*?'
        r'class="article-contributor-section_link" href="([^"]*)"',
        html, re.DOTALL
    ))

    seen_names = set()
    authors_raw = []
    translators_raw = []

    for block in contrib_blocks:
        name_raw = clean_text(block.group(1))
        bio_text = clean_text(block.group(2))
        profile_url = block.group(3).strip() or None

        is_translator = name_raw.lower().startswith('translated by')
        name = re.sub(r'(?i)^translated by\s+', '', name_raw).strip()

        if name in seen_names:
            continue
        seen_names.add(name)

        entry = {
            "display_name": name,
            "author_url": profile_url,
            "bio": bio_text or None,
        }
        (translators_raw if is_translator else authors_raw).append(entry)

    # Fallback: inline byline
    if not authors_raw:
        byline_m = re.search(
            r'class="article-twenty-twenty-style-contributor">\s*'
            r'<a[^>]*href="https://granta\.com/contributor/([^/]+)/"[^>]*>([^<]+)</a>',
            html
        )
        if byline_m:
            authors_raw.append({
                "display_name": clean_text(byline_m.group(2)),
                "author_url": f"https://granta.com/contributor/{byline_m.group(1)}/",
                "bio": None,
            })
            notes.append("author_bio_not_found: byline fallback used")
        else:
            meta_auth_m = re.search(r'<meta name="author" content="([^"]+)"', html)
            if meta_auth_m:
                authors_raw.append({
                    "display_name": clean_text(meta_auth_m.group(1)),
                    "author_url": None,
                    "bio": None,
                })
                notes.append("author_bio_not_found: meta author fallback used")
            else:
                notes.append("manual_review: author not found")

    # Translator summary fields
    translator_names = [t["display_name"] for t in translators_raw] or None
    translator_bios  = [t["bio"] for t in translators_raw] or None

    # ── Article body ──────────────────────────────────────────────────────────
    body_html = None
    body_text = None

    # Granta uses two different page templates:
    #
    # NEW (2020+): div class contains 'article-twenty-twenty-style-content'
    #   end boundary: 'article-contributor-section_title' or 'article-contributor--bottom'
    #
    # OLD (pre-2020): div class is 'col-lg-8 article-content' (+ optional modifiers)
    #   end boundary: 'article-contributor-photo-section'
    #
    # Both use a depth-counting extractor to handle nested divs correctly.

    def extract_div_inner(html, start_pos):
        """Given the position just after a <div ...> opening tag, extract its
        full inner content by counting nested div open/close tags."""
        depth = 1
        pos = 0
        src = html[start_pos:]
        while pos < len(src) and depth > 0:
            open_m  = re.search(r'<div[^>]*>', src[pos:])
            close_m = re.search(r'</div>', src[pos:])
            if open_m and (not close_m or open_m.start() < close_m.start()):
                depth += 1
                pos += open_m.start() + len(open_m.group())
            elif close_m:
                depth -= 1
                pos += close_m.start() + len(close_m.group())
            else:
                break
        return src[:pos]

    def find_end_boundary(html, markers):
        """Return the position of the opening <div just before the first marker found."""
        for marker in markers:
            idx = html.find(marker)
            if idx > 0:
                div_start = html.rfind('<div', 0, idx)
                return div_start if div_start > 0 else idx
        return len(html)

    # ── Try NEW template first ─────────────────────────────────────────────────
    is_new_template = 'article-twenty-twenty-style-content' in html

    if is_new_template:
        end_boundary = find_end_boundary(html, [
            'article-contributor--bottom',
            'article-contributor-section_title',
            'id="comments"',
        ])
        article_region = html[:end_boundary]

        title_meta_m = re.search(
            r'<div[^>]*class=["\']article-twenty-twenty-style-title-meta["\'][^>]*>',
            article_region
        )
        prose_start_m = re.search(
            r'<div[^>]*class=["\'][^"\']* ?article-twenty-twenty-style-content[^"\']* ?["\'][^>]*>',
            article_region
        )

        if prose_start_m:
            title_inner = extract_div_inner(article_region, title_meta_m.end()) if title_meta_m else ""
            prose_inner = extract_div_inner(article_region, prose_start_m.end())
            title_block = clean_html(title_inner)
            prose_block = clean_html(prose_inner)
            body_html = (title_block + "\n\n" + prose_block).strip() if title_block else prose_block
            body_text = ' '.join(strip_tags(body_html).split())
            notes.append("template:new")

    # ── Try OLD template ───────────────────────────────────────────────────────
    if not body_html:
        # Old template: 'col-lg-8 article-content' with optional modifier classes
        old_content_m = re.search(
            r'<div[^>]*class="col-lg-8 article-content[^"]*"[^>]*>',
            html
        )
        if old_content_m:
            end_boundary = find_end_boundary(html, [
                'article-contributor-photo-section',
                'article-contributor-section_title',
                'id="comments"',
            ])
            article_region = html[:end_boundary]
            prose_inner = extract_div_inner(article_region, old_content_m.end())
            body_html = clean_html(prose_inner)
            body_text = ' '.join(strip_tags(body_html).split())
            notes.append("template:old")

    # ── Last resort: all <p> tags inside <article> tag ────────────────────────
    if not body_html:
        article_m = re.search(r'<article[^>]*>(.*?)</article>', html, re.DOTALL)
        if article_m:
            paras = re.findall(r'<p[^>]*>(.*?)</p>', article_m.group(1), re.DOTALL)
            if paras:
                body_html = '\n'.join(f'<p>{clean_html(p)}</p>' for p in paras)
                body_text = ' '.join(clean_text(p) for p in paras)
                notes.append("template:paragraph-fallback")

    if not body_html:
        notes.append("manual_review: article body not found")

    # ── Issue context ─────────────────────────────────────────────────────────
    if issue_context:
        issue_data = {
            "issue_url": issue_context.get("issue_url"),
            "issue_label": issue_context.get("issue_label"),
            "issue_number": issue_context.get("issue_number"),
            "issue_date": issue_context.get("issue_date"),
        }
    else:
        granta_num_m = re.search(r'Granta (\d+)', html)
        issue_data = {
            "issue_url": None,
            "issue_label": f"Granta {granta_num_m.group(1)}" if granta_num_m else None,
            "issue_number": int(granta_num_m.group(1)) if granta_num_m else None,
            "issue_date": None,
        }

    # ── Assemble ──────────────────────────────────────────────────────────────
    return {
        "journal": {"name": "Granta", "slug": "granta"},
        "issue": issue_data,
        "piece": {
            "original_url": url,
            "canonical_url": canonical,
            "source_slug": slug_from_url(url),
            "title_display": title_display,
            "title_tag": title_tag,
            "piece_type": piece_type,
            "edition": edition,
            "keywords": keywords,
            "date_published_raw": date_raw,
            "date_published_display": date_display,
            "meta_description": meta_desc,
            "author": authors_raw[0]["display_name"] if authors_raw else None,
            "translators": translator_names,
        },
        "authors_raw": [
            {"display_name": a["display_name"], "author_url": a["author_url"]}
            for a in authors_raw
        ],
        "translators_raw": [
            {"display_name": t["display_name"], "author_url": t["author_url"]}
            for t in translators_raw
        ],
        "derived": {
            "author_bio_raw": authors_raw[0]["bio"] if authors_raw else None,
            "author_bios_raw": [a["bio"] for a in authors_raw],
            "translator_bio_raw": translators_raw[0]["bio"] if translators_raw else None,
            "translator_bios_raw": translator_bios or [],
        },
        "content": {
            "text": body_text,
            "html": body_html,
        },
        "page_metadata": {
            "canonical_url": canonical,
            "meta_description": meta_desc,
            "keywords": keywords,
        },
        "scrape_meta": {
            "scraped_at_utc": now_utc(),
            "scraper_version": SCRAPER_VERSION,
            "notes": notes,
        },
    }


# ─── Runner ───────────────────────────────────────────────────────────────────

def scrape_single(url, issue_context=None, save=True, base_out_dir="granta_pieces"):
    print(f"  Fetching: {url}")
    try:
        html = fetch(url)
    except Exception as e:
        print(f"  ERROR fetching {url}: {e}")
        return None

    if not html or len(html) < 5000:
        print(f"  ERROR: Empty or too-short response for {url}")
        return None

    try:
        result = parse_piece(url, html, issue_context)
    except Exception as e:
        print(f"  ERROR parsing {url}: {e}")
        return None

    if save:
        # Determine output directory
        iss = result.get("issue", {})
        dir_name = issue_dir_name(iss.get("issue_number"), iss.get("issue_label") or "")
        out_dir = os.path.join(base_out_dir, dir_name)
        os.makedirs(out_dir, exist_ok=True)

        slug = result["piece"]["source_slug"]
        author_name = result["piece"].get("author", "")
        fname = piece_filename(slug, author_name)
        out_path = os.path.join(out_dir, f"{fname}.json")
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        notes = result['scrape_meta']['notes']
        flag = " ⚠ REVIEW" if any('manual_review' in n for n in notes) else ""
        print(f"  ✓ {result['piece']['title_display']} → {out_path}{flag}")

    return result


def scrape_issue(issue, delay=0.5, base_out_dir="granta_pieces"):
    """Scrape all free pieces in one issue dict."""
    issue_context_base = {
        "issue_url": issue["issue_url"],
        "issue_label": issue["issue_label"],
        "issue_number": issue["issue_number"],
        "issue_date": issue["issue_date"],
    }

    results = []
    pieces = issue.get("pieces", [])
    for i, piece in enumerate(pieces):
        ctx = {
            **issue_context_base,
            "type": piece.get("type"),
            "edition": piece.get("edition", "Online Edition"),
        }
        result = scrape_single(piece["url"], issue_context=ctx,
                               save=True, base_out_dir=base_out_dir)
        if result:
            results.append(result)
        if i < len(pieces) - 1:
            time.sleep(delay)

    return results


def main():
    parser = argparse.ArgumentParser(description="Granta piece scraper v" + SCRAPER_VERSION)
    parser.add_argument('--url', help='Single piece URL to scrape')
    parser.add_argument('--issue-json', help='Path to granta_issues.json')
    parser.add_argument('--issue-number', type=int,
                        help='Scrape a specific issue number from the JSON')
    parser.add_argument('--all', action='store_true',
                        help='Scrape all issues in the JSON')
    parser.add_argument('--delay', type=float, default=0.5,
                        help='Seconds between requests (default 0.5)')
    parser.add_argument('--out-dir', default='granta_pieces',
                        help='Base output directory (default: granta_pieces/)')
    args = parser.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    if args.url:
        scrape_single(args.url, base_out_dir=args.out_dir)

    elif args.issue_json:
        with open(args.issue_json, encoding='utf-8') as f:
            data = json.load(f)

        issues = data['issues']

        if args.issue_number:
            issues = [i for i in issues if i['issue_number'] == args.issue_number]
            if not issues:
                print(f"Issue {args.issue_number} not found in JSON.")
                sys.exit(1)

        for issue in issues:
            print(f"\n── {issue['issue_label']} ({issue['issue_date']}) ──")
            scrape_issue(issue, delay=args.delay, base_out_dir=args.out_dir)

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
