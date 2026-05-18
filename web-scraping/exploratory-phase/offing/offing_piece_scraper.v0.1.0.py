"""
offing_piece_scraper.v0.1.0.py
================================
Scraper for individual pieces published by The Offing (theoffingmag.com).

The Offing publishes by department (Essay, Fiction, Poetry, etc.) rather
than by issue. This scraper fetches piece pages, extracts structured
metadata, author/translator bios with personal URLs, and the full body
text — then writes one JSON file per piece.

Schema is modelled on the Kopani Kopani canonical piece schema (see
anderson_lifes-a-ratchet_f-w.json / folding-your-mother-govil.json).

Output path:
  offing_pieces/{department}/{author-surname}_{piece-slug}.json

Usage
-----
  # Single URL:
  python offing_piece_scraper.v0.1.0.py --url https://theoffingmag.com/essay/brother-she-calls-me/

  # All pieces from a department JSON (e.g. the_offing_essays.json):
  python offing_piece_scraper.v0.1.0.py --dept-json the_offing_essays.json

  # Limit to first N pieces:
  python offing_piece_scraper.v0.1.0.py --dept-json the_offing_essays.json --limit 5

  # Overwrite already-scraped files:
  python offing_piece_scraper.v0.1.0.py --dept-json the_offing_essays.json --overwrite

  # Custom output directory:
  python offing_piece_scraper.v0.1.0.py --dept-json the_offing_essays.json --out ./my_output

  # Delay between requests (seconds, default 1.5):
  python offing_piece_scraper.v0.1.0.py --dept-json the_offing_essays.json --delay 2.0

Key HTML selectors (theoffingmag.com WordPress theme "the-offing"):
  Title          : h1.entry-title
  Subtitle       : p.entry-subtitle  (optional)
  Department     : p.entry-category
  Byline author  : span.byline > a   (text + href)
  Published date : span.posted-on    (display) + meta[article:published_time] (ISO)
  Body           : div.entry-content
  Author bio     : p.entry-byline    (outside entry-content, after <hr class="single">)
  Contributor pg : theoffingmag.com/contributor/{slug}/
    Bio text     : div.entry-content.author  (plain text block)
    Social link  : p.social-link > a         (href = personal URL or Twitter)

Notes on known quirks:
  - meta[name="author"] contains the WP backend username (e.g. "steffan",
    "Christine Lee"), NOT the byline author. We ignore it.
  - "From the Archives:" pieces carry a note inside the body like:
    "This essay was originally published on [date]." — captured in
    piece.archive_original_published.
  - Some pieces have a subtitle (p.entry-subtitle) beneath the h1.
  - article:tag keywords are absent from most Offing pages; keywords field
    will be empty [] in those cases.
  - Contributor profile pages append a <p class="social-link"> with the
    author's personal URL or social handle — this is captured in
    authors_raw[n].contributor_url_offing and authors_raw[n].personal_url.
  - Co-authored pieces list multiple span.byline blocks or comma-separated
    names; the scraper handles both patterns.
  - The body div contains a featured image <figure> and an inner
    <div class="col-9 ..."> — text is extracted from the inner div,
    skipping figures, captions, and social share widgets.
"""

SCRAPER_VERSION = "0.1.0"

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

# ---------------------------------------------------------------------------
# Tiny HTML parser (no external deps — stdlib only)
# ---------------------------------------------------------------------------

try:
    from html.parser import HTMLParser
except ImportError:
    raise SystemExit("Python stdlib html.parser not found — unexpected.")

# We use a lightweight recursive-descent approach via HTMLParser to build
# a simple node tree, then query it with CSS-like helpers.

class Node:
    """Minimal DOM node."""
    __slots__ = ("tag", "attrs", "children", "text", "tail", "parent")

    def __init__(self, tag, attrs=None):
        self.tag = tag.lower() if tag else tag
        self.attrs = {k.lower(): v for k, v in (attrs or [])}
        self.children = []
        self.text = ""   # text immediately inside this element before first child
        self.tail = ""   # text after closing tag (before next sibling)
        self.parent = None

    def get(self, attr, default=None):
        return self.attrs.get(attr, default)

    def has_class(self, cls):
        classes = self.attrs.get("class", "").split()
        return cls in classes

    def find(self, tag=None, cls=None, attr=None, attr_val=None):
        """Depth-first search; returns first match or None."""
        for node in self._iter():
            if self._matches(node, tag, cls, attr, attr_val):
                return node
        return None

    def findall(self, tag=None, cls=None, attr=None, attr_val=None):
        """Depth-first search; returns all matches."""
        return [n for n in self._iter() if self._matches(n, tag, cls, attr, attr_val)]

    def _matches(self, node, tag, cls, attr, attr_val):
        if tag and node.tag != tag.lower():
            return False
        if cls and not node.has_class(cls):
            return False
        if attr:
            if attr_val is not None:
                if node.attrs.get(attr) != attr_val:
                    return False
            else:
                if attr not in node.attrs:
                    return False
        return True

    def _iter(self):
        """Iterate over all descendants (depth-first, not self)."""
        stack = list(self.children)
        while stack:
            n = stack.pop(0)
            yield n
            stack = list(n.children) + stack

    def inner_text(self, skip_tags=None):
        """Recursively collect all text content."""
        skip_tags = set(t.lower() for t in (skip_tags or []))
        parts = []
        self._collect_text(self, parts, skip_tags)
        return "".join(parts)

    def _collect_text(self, node, parts, skip_tags):
        if node.tag in skip_tags:
            return
        if node.text:
            parts.append(node.text)
        for child in node.children:
            self._collect_text(child, parts, skip_tags)
            if child.tail:
                parts.append(child.tail)

    def inner_html(self):
        """Reconstruct inner HTML (best-effort)."""
        parts = []
        if self.text:
            parts.append(self.text)
        for child in self.children:
            parts.append(child._to_html())
        return "".join(parts)

    def _to_html(self):
        attrs = ""
        for k, v in self.attrs.items():
            if v is None:
                attrs += f" {k}"
            else:
                attrs += f' {k}="{v}"'
        inner = self.inner_html()
        result = f"<{self.tag}{attrs}>{inner}</{self.tag}>"
        if self.tail:
            result += self.tail
        return result

    def __repr__(self):
        return f"<Node {self.tag} class='{self.attrs.get('class','')}' text={self.text[:30]!r}>"


# Void elements that have no closing tag
VOID_ELEMENTS = {
    "area","base","br","col","embed","hr","img","input",
    "link","meta","param","source","track","wbr",
}


class OffingHTMLParser(HTMLParser):
    """Build a simple node tree from HTML."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("__root__")
        self._stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs)
        parent = self._stack[-1]
        node.parent = parent
        parent.children.append(node)
        if tag.lower() not in VOID_ELEMENTS:
            self._stack.append(node)

    def handle_endtag(self, tag):
        # Pop until we find the matching open tag (handles malformed HTML)
        for i in range(len(self._stack) - 1, 0, -1):
            if self._stack[i].tag == tag.lower():
                self._stack = self._stack[:i]
                break

    def handle_data(self, data):
        current = self._stack[-1]
        if current.children:
            current.children[-1].tail = (current.children[-1].tail or "") + data
        else:
            current.text = (current.text or "") + data


def parse_html(html: str) -> Node:
    parser = OffingHTMLParser()
    parser.feed(html)
    return parser.root


# ---------------------------------------------------------------------------
# HTTP fetch with urllib (cross-platform, no deps)
# ---------------------------------------------------------------------------

def fetch_url(url: str, timeout: int = 20) -> tuple[str, str]:
    """
    Fetch URL, ensure trailing slash (WordPress canonical), follow redirects.
    Returns (final_url, html_text).
    """
    # Ensure trailing slash on path (skip if there's a query string)
    parsed = urllib.parse.urlparse(url)
    if parsed.path and not parsed.path.endswith("/") and "." not in parsed.path.split("/")[-1]:
        url = urllib.parse.urlunparse(parsed._replace(path=parsed.path + "/"))

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (compatible; KopaniScraper/0.1; "
                "+https://github.com/kopani)"
            ),
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        # Detect charset from Content-Type header
        content_type = resp.headers.get_content_type()
        charset = resp.headers.get_content_charset("utf-8")
        raw = resp.read()
        html = raw.decode(charset, errors="replace")
        final_url = resp.url
    return final_url, html


# ---------------------------------------------------------------------------
# Slug / filename helpers
# ---------------------------------------------------------------------------

def slugify(text: str) -> str:
    """Simple ASCII slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def extract_slug_from_url(url: str) -> str:
    """Extract the last non-empty path segment."""
    path = urllib.parse.urlparse(url).path.rstrip("/")
    return path.split("/")[-1] if path else ""


def extract_surname(display_name: str) -> str:
    """
    Best-effort surname extraction for filename prefix.
    Handles 'Wang Ping' → 'ping', 'Nwanne Agwu' → 'agwu',
    '[Sarah] Cavar' → 'cavar'.
    """
    # Strip brackets e.g. [Sarah]
    name = re.sub(r"\[.*?\]", "", display_name).strip()
    parts = name.split()
    if parts:
        return slugify(parts[-1])
    return slugify(display_name)


def build_output_filename(department: str, authors_raw: list, piece_slug: str) -> str:
    """
    offing_pieces/{department}/{surname}_{piece-slug}.json
    For co-authored pieces, use first author's surname.
    """
    dept = slugify(department) if department else "unknown"
    if authors_raw:
        surname = extract_surname(authors_raw[0].get("display_name", "unknown"))
    else:
        surname = "unknown"
    return os.path.join("offing_pieces", dept, f"{surname}_{piece_slug}.json")


# ---------------------------------------------------------------------------
# Contributor profile scraper
# ---------------------------------------------------------------------------

def scrape_contributor_profile(contributor_url: str, timeout: int = 20) -> dict:
    """
    Fetch theoffingmag.com/contributor/{slug}/ and extract:
      - bio_text (plain text, no HTML)
      - personal_url (from p.social-link > a, if present)
      - social_label (e.g. "VISIT", "FOLLOW")
    Returns {} on failure.
    """
    if not contributor_url:
        return {}
    try:
        _, html = fetch_url(contributor_url, timeout=timeout)
    except Exception as e:
        return {"_error": str(e)}

    root = parse_html(html)

    # div.entry-content.author
    bio_div = root.find("div", cls="author")
    if not bio_div:
        return {}

    # Extract social link before stripping it from text
    social_link_node = bio_div.find("p", cls="social-link")
    personal_url = None
    social_label = None
    if social_link_node:
        a = social_link_node.find("a")
        if a:
            personal_url = a.get("href")
            # Label is only the direct text of p.social-link (not children)
            # to avoid pulling in leaked article listing HTML
            raw_label = (social_link_node.text or "").strip()
            # Append text of any direct <br> tails (they carry "VISIT" etc)
            for child in social_link_node.children:
                if child.tag == "br" and child.tail:
                    raw_label += " " + child.tail.strip()
                elif child.tag == "a":
                    break  # stop before the link itself
            # Normalise whitespace and strip trailing link text
            raw_label = re.sub(r"\s+", " ", raw_label).strip()
            link_text = a.inner_text().strip()
            if link_text and raw_label.endswith(link_text):
                raw_label = raw_label[: -len(link_text)].strip()
            # Only keep short labels ("VISIT", "FOLLOW Nwanne") — discard bleed
            if len(raw_label) > 60:
                raw_label = ""
            social_label = raw_label or None

    # Bio plain text: collect text from bio_div, stopping at the first
    # <article> or <section> child (they leak in via unclosed WP tags),
    # and skipping p.social-link.
    bio_parts = []
    if bio_div.text:
        bio_parts.append(bio_div.text)
    for child in bio_div.children:
        # Stop at article listing bleed
        if child.tag in ("article", "section", "header", "footer", "ul", "ol"):
            break
        if child.tag == "p" and child.has_class("social-link"):
            continue
        bio_parts.append(child.inner_text())
        if child.tail:
            bio_parts.append(child.tail)

    bio_text = re.sub(r"\s+", " ", "".join(bio_parts)).strip()

    return {
        "bio_text": bio_text or None,
        "personal_url": personal_url,
        "social_label": social_label,
    }


# ---------------------------------------------------------------------------
# Main piece scraper
# ---------------------------------------------------------------------------

def scrape_piece(url: str, timeout: int = 20) -> dict:
    """
    Scrape one Offing piece page. Returns the full output dict.
    Logs issues into scrape_meta.notes.
    """
    notes = []
    final_url, html = fetch_url(url, timeout=timeout)
    root = parse_html(html)
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # ------------------------------------------------------------------
    # HEAD / meta
    # ------------------------------------------------------------------
    head = root.find("head")

    def meta_content(prop_attr, prop_val):
        if not head:
            return None
        for m in head.findall("meta"):
            if m.get(prop_attr) == prop_val:
                return m.get("content")
        return None

    canonical_url = None
    if head:
        link_canon = head.find("link", attr="rel", attr_val="canonical")
        if link_canon:
            canonical_url = link_canon.get("href")

    og_title        = meta_content("property", "og:title")
    og_description  = meta_content("property", "og:description")
    og_image        = meta_content("property", "og:image")
    og_type         = meta_content("property", "og:type")
    pub_time_iso    = meta_content("property", "article:published_time")
    mod_time_iso    = meta_content("property", "article:modified_time")
    reading_time    = meta_content("name", "twitter:data2")  # e.g. "14 minutes"

    # Keywords — article:tag (often absent on Offing)
    keywords = []
    if head:
        for m in head.findall("meta", attr="property", attr_val="article:tag"):
            v = m.get("content")
            if v:
                keywords.append(v)

    # Page <title>
    title_tag_text = None
    if head:
        t = head.find("title")
        if t:
            title_tag_text = (t.text or "").strip()
            # Strip site name suffix " - The Offing"
            title_tag_text = re.sub(r"\s*[-–|]\s*The Offing\s*$", "", title_tag_text).strip()

    # ------------------------------------------------------------------
    # Article element
    # ------------------------------------------------------------------
    article = root.find("article")
    if not article:
        notes.append("article_element_not_found")
        article = root  # fallback to whole doc

    # Department / type
    dept_node = article.find("p", cls="entry-category")
    department = dept_node.inner_text().strip().title() if dept_node else None
    if not department:
        # Try inferring from URL path  e.g. /essay/slug/
        path_parts = [p for p in urllib.parse.urlparse(final_url).path.split("/") if p]
        if len(path_parts) >= 2:
            department = path_parts[0].title()
        notes.append("department_inferred_from_url")

    # Title
    h1 = article.find("h1", cls="entry-title")
    title_display = h1.inner_text().strip() if h1 else title_tag_text
    if not title_display:
        notes.append("title_not_found")

    # Subtitle (optional)
    subtitle_node = article.find("p", cls="entry-subtitle")
    subtitle = subtitle_node.inner_text().strip() if subtitle_node else None
    if not subtitle:
        subtitle = None

    # Piece slug from canonical URL
    piece_slug = extract_slug_from_url(canonical_url or final_url)

    # ------------------------------------------------------------------
    # Authors — handle multiple span.byline blocks
    # ------------------------------------------------------------------
    byline_nodes = article.findall("span", cls="byline")
    authors_raw = []
    for bn in byline_nodes:
        a_tag = bn.find("a")
        if a_tag:
            display_name = a_tag.inner_text().strip().title()
            contributor_url = a_tag.get("href")
        else:
            # No link — plain text after "By "
            raw = bn.inner_text().strip()
            display_name = re.sub(r"^[Bb]y\s+", "", raw).strip().title()
            contributor_url = None
        if display_name:
            authors_raw.append({
                "display_name": display_name,
                "contributor_url_offing": contributor_url,
                "personal_url": None,
                "social_label": None,
            })

    if not authors_raw:
        notes.append("byline_not_found")

    # Also check for translator credits — look for text like "Translated by"
    # in the entry-meta or body header area
    translators_raw = []
    entry_meta = article.find("div", cls="entry-meta")
    if entry_meta:
        meta_text = entry_meta.inner_text()
        trans_match = re.search(r"[Tt]ranslat(?:ed|ion)\s+by\s+(.+?)(?:\s*\||$)", meta_text)
        if trans_match:
            raw_names = trans_match.group(1).strip()
            # Handle "A and B" or "A, B"
            parts = re.split(r"\s+and\s+|,\s*", raw_names)
            for p in parts:
                p = p.strip().title()
                if p:
                    translators_raw.append({
                        "display_name": p,
                        "contributor_url_offing": None,
                        "personal_url": None,
                        "social_label": None,
                    })

    # ------------------------------------------------------------------
    # Publication date
    # ------------------------------------------------------------------
    posted_on = article.find("span", cls="posted-on")
    date_display = posted_on.inner_text().strip() if posted_on else None

    # Normalise ISO date
    date_published_iso = None
    if pub_time_iso:
        try:
            # article:published_time is like "2021-09-30T05:00:39+00:00"
            date_published_iso = pub_time_iso[:10]  # "2021-09-30"
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Body text
    # ------------------------------------------------------------------
    entry_content = article.find("div", cls="entry-content")

    body_text = ""
    body_html = ""
    archive_original_published = None

    if entry_content:
        body_html = entry_content.inner_html()

        # The real prose lives inside the inner col-9 div (skips featured img)
        inner_col = entry_content.find("div", cls="col-9")
        text_source = inner_col if inner_col else entry_content

        # Extract paragraphs — skip figure/figcaption, script, style, svg
        SKIP = {"figure", "figcaption", "script", "style", "svg",
                "noscript", "form", "nav", "footer", "header"}
        prose_parts = []

        def collect_prose(node, parts):
            if node.tag in SKIP:
                return
            # Social share widgets often have class "sharedaddy" or "sd-block"
            classes = node.attrs.get("class", "")
            if any(c in classes for c in ["sharedaddy", "sd-block", "sd-social",
                                           "jp-relatedposts", "wpcnt"]):
                return
            if node.text and node.text.strip():
                parts.append(node.text.strip())
            for child in node.children:
                collect_prose(child, parts)
                if child.tail and child.tail.strip():
                    parts.append(child.tail.strip())

        # Walk top-level children of text_source
        para_texts = []
        for child in text_source.children:
            if child.tag in SKIP:
                continue
            classes = child.attrs.get("class", "")
            if any(c in classes for c in ["sharedaddy", "sd-block", "jp-relatedposts"]):
                continue
            para_text = child.inner_text(skip_tags=SKIP).strip()
            if para_text:
                para_texts.append(para_text)

        body_text = "\n\n".join(para_texts)

        # Detect "From the Archives" original publication note
        # Pattern: "This essay/story/poem was originally published on [date]."
        archive_match = re.search(
            r"[Tt]his\s+\w+\s+was\s+originally\s+published\s+(?:on\s+)?(.+?)[\.\,]",
            body_text,
        )
        if archive_match:
            archive_original_published = archive_match.group(0).strip()
            notes.append("from_the_archives")
    else:
        notes.append("entry_content_not_found")

    # Is this a "From the Archives" piece?
    is_archive = (
        title_display is not None and
        title_display.lower().startswith("from the archives")
    ) or "from_the_archives" in notes

    # Clean title: strip "From the Archives: " prefix for source_title
    source_title = title_display or ""
    if is_archive:
        source_title = re.sub(r"^[Ff]rom\s+the\s+[Aa]rchives\s*:\s*", "", source_title).strip()

    # ------------------------------------------------------------------
    # Author bios — from p.entry-byline (on the piece page)
    # ------------------------------------------------------------------
    # p.entry-byline appears outside entry-content, after the <hr class="single">
    bio_nodes = article.findall("p", cls="entry-byline")
    # Also check the whole doc (sometimes it's outside <article>)
    if not bio_nodes:
        bio_nodes = root.findall("p", cls="entry-byline")

    author_bios_raw = []
    for bn in bio_nodes:
        bio_text = bn.inner_text(skip_tags={"script", "style", "svg"}).strip()
        bio_text = re.sub(r"\s+", " ", bio_text)
        if bio_text:
            author_bios_raw.append(bio_text)

    # Also scrape contributor profile pages for personal URLs + richer bios
    for i, author in enumerate(authors_raw):
        contrib_url = author.get("contributor_url_offing")
        if contrib_url:
            profile = scrape_contributor_profile(contrib_url, timeout=timeout)
            if "_error" in profile:
                notes.append(f"contributor_profile_fetch_error:{author['display_name']}")
            else:
                if profile.get("personal_url"):
                    authors_raw[i]["personal_url"] = profile["personal_url"]
                if profile.get("social_label"):
                    authors_raw[i]["social_label"] = profile["social_label"]
                # Use profile bio if we didn't get one from the piece page
                if profile.get("bio_text") and i >= len(author_bios_raw):
                    author_bios_raw.append(profile["bio_text"])

    for i, trans in enumerate(translators_raw):
        contrib_url = trans.get("contributor_url_offing")
        if contrib_url:
            profile = scrape_contributor_profile(contrib_url, timeout=timeout)
            if "_error" not in profile:
                if profile.get("personal_url"):
                    translators_raw[i]["personal_url"] = profile["personal_url"]

    # Primary author convenience field
    primary_author = authors_raw[0]["display_name"] if authors_raw else None
    primary_author_bio = author_bios_raw[0] if author_bios_raw else None

    # ------------------------------------------------------------------
    # Assemble output
    # ------------------------------------------------------------------
    output = {
        "journal": {
            "name": "The Offing",
            "slug": "the-offing",
        },
        "department": {
            "name": department,
            "department_url": None,  # populated below if inferrable
        },
        "piece": {
            "original_url": url,
            "canonical_url": canonical_url or final_url,
            "source_slug": piece_slug,
            "title_display": title_display,
            "title_tag": title_tag_text,
            "subtitle": subtitle,
            "piece_type": department,
            "keywords": keywords,
            "date_published_raw": pub_time_iso,
            "date_published_display": date_display,
            "date_published_iso": date_published_iso,
            "date_modified_raw": mod_time_iso,
            "meta_description": og_description,
            "og_image": og_image,
            "reading_time": reading_time,
            "author": primary_author,
            "translators": (
                ", ".join(t["display_name"] for t in translators_raw)
                if translators_raw else None
            ),
            "is_archive": is_archive,
            "archive_original_published": archive_original_published,
        },
        "authors_raw": [
            {
                "display_name": a["display_name"],
                "contributor_url_offing": a.get("contributor_url_offing"),
                "personal_url": a.get("personal_url"),
                "social_label": a.get("social_label"),
            }
            for a in authors_raw
        ],
        "translators_raw": [
            {
                "display_name": t["display_name"],
                "contributor_url_offing": t.get("contributor_url_offing"),
                "personal_url": t.get("personal_url"),
            }
            for t in translators_raw
        ],
        "derived": {
            "author_bio_raw": primary_author_bio,
            "author_bios_raw": author_bios_raw,
            "translator_bio_raw": None,
            "translator_bios_raw": [],
        },
        "content": {
            "text": body_text,
            "html": body_html,
        },
        "page_metadata": {
            "canonical_url": canonical_url,
            "meta_description": og_description,
            "keywords": keywords,
            "og_title": og_title,
            "og_type": og_type,
            "og_image": og_image,
        },
        "scrape_meta": {
            "scraped_at_utc": now_utc,
            "scraper_version": SCRAPER_VERSION,
            "notes": notes,
        },
    }

    # Fill department URL
    if department:
        dept_slug = slugify(department)
        output["department"]["department_url"] = (
            f"https://theoffingmag.com/{dept_slug}/"
        )

    return output


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args():
    p = argparse.ArgumentParser(
        description="Scrape individual piece pages from The Offing magazine.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    source = p.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "--url",
        help="Single piece URL to scrape.",
    )
    source.add_argument(
        "--dept-json",
        metavar="FILE",
        help=(
            "Path to a department JSON file (e.g. the_offing_essays.json) "
            "whose 'essays' / 'fiction' / 'poetry' array contains piece "
            "objects with 'url' keys."
        ),
    )

    p.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="Maximum number of pieces to scrape (default: all).",
    )
    p.add_argument(
        "--delay",
        type=float,
        default=1.5,
        metavar="SECONDS",
        help="Delay between requests in seconds (default: 1.5).",
    )
    p.add_argument(
        "--out",
        default=".",
        metavar="DIR",
        help=(
            "Base output directory. Files are written to "
            "{out}/offing_pieces/{dept}/{file}.json (default: current dir)."
        ),
    )
    p.add_argument(
        "--overwrite",
        action="store_true",
        help="Re-scrape and overwrite already-scraped files.",
    )
    return p.parse_args()


def load_dept_json(path: str) -> list:
    """
    Load a department JSON and return the list of piece objects.
    Supports top-level keys: 'essays', 'fiction', 'poetry', 'pieces'.
    """
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    for key in ("essays", "fiction", "poetry", "art", "criticism",
                "hybrid", "translation", "pieces"):
        if key in data and isinstance(data[key], list):
            return data[key]
    # Fallback: if root is a list
    if isinstance(data, list):
        return data
    raise ValueError(
        f"Cannot find a piece list in {path}. "
        f"Expected one of: essays, fiction, poetry, pieces."
    )


def run():
    args = parse_args()
    base_out = Path(args.out)

    pieces = []
    if args.url:
        pieces = [{"url": args.url, "type": None, "author": None}]
    else:
        pieces = load_dept_json(args.dept_json)

    if args.limit:
        pieces = pieces[: args.limit]

    total = len(pieces)
    scraped = 0
    skipped = 0
    errors = 0

    for idx, piece_meta in enumerate(pieces, 1):
        url = piece_meta.get("url")
        if not url:
            print(f"[{idx}/{total}] SKIP — no URL in piece entry: {piece_meta}")
            skipped += 1
            continue

        # Determine output path early so we can skip if exists
        # We don't know department yet without fetching, so we do a quick
        # path check based on the piece_meta if available
        dept_hint = (
            piece_meta.get("type") or
            piece_meta.get("department") or
            ""
        ).lower().strip()
        author_hint = piece_meta.get("author", "unknown")
        slug_hint = extract_slug_from_url(url)

        if dept_hint and author_hint:
            surname_hint = extract_surname(author_hint)
            out_rel = os.path.join(
                "offing_pieces", dept_hint,
                f"{surname_hint}_{slug_hint}.json"
            )
            out_path = base_out / out_rel
        else:
            out_path = None

        if out_path and out_path.exists() and not args.overwrite:
            print(f"[{idx}/{total}] SKIP (exists) — {out_path}")
            skipped += 1
            continue

        print(f"[{idx}/{total}] Scraping — {url}")
        try:
            result = scrape_piece(url)
        except urllib.error.HTTPError as e:
            print(f"  ERROR HTTP {e.code}: {e.reason}")
            errors += 1
            if idx < total:
                time.sleep(args.delay)
            continue
        except urllib.error.URLError as e:
            print(f"  ERROR URL: {e.reason}")
            errors += 1
            if idx < total:
                time.sleep(args.delay)
            continue
        except Exception as e:
            print(f"  ERROR: {e}")
            errors += 1
            if idx < total:
                time.sleep(args.delay)
            continue

        # Build final output path from scraped data
        department = result["piece"].get("piece_type") or dept_hint or "unknown"
        authors = result.get("authors_raw", [])
        piece_slug = result["piece"].get("source_slug") or slug_hint

        out_rel = build_output_filename(department, authors, piece_slug)
        out_path = base_out / out_rel

        # Final overwrite check (now with real dept)
        if out_path.exists() and not args.overwrite:
            print(f"  SKIP (exists) — {out_path}")
            skipped += 1
            if idx < total:
                time.sleep(args.delay)
            continue

        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        notes = result["scrape_meta"]["notes"]
        note_str = f"  notes: {notes}" if notes else ""
        body_len = len(result["content"]["text"])
        print(f"  → {out_path}  ({body_len} chars body){note_str}")
        scraped += 1

        if idx < total:
            time.sleep(args.delay)

    print(
        f"\nDone. {scraped} scraped, {skipped} skipped, {errors} errors "
        f"(of {total} total)."
    )


if __name__ == "__main__":
    run()
