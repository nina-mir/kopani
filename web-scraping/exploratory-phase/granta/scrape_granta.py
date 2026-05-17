import re
import json
import subprocess
import time

HEADERS = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

ISSUE_URLS = [
    "https://granta.com/products/granta-174-therapy/",
    "https://granta.com/products/granta-173-india/",
    "https://granta.com/products/granta-172-badlands/",
    "https://granta.com/products/granta-171-dead-friends/",
    "https://granta.com/products/granta-170-winners/",
    "https://granta.com/products/granta-169-china/",
    "https://granta.com/products/granta-168-significant-other/",
    "https://granta.com/products/granta-167-extraction/",
    "https://granta.com/products/granta-166-generations/",
    "https://granta.com/products/granta-165-deutschland/",
    "https://granta.com/products/granta-164-last-notes/",
    "https://granta.com/products/granta-163-best-of-young-british-novelists-5/",
    "https://granta.com/products/granta-162-definitive-narratives-of-escape/",
    "https://granta.com/products/granta-161-sister-brother/",
    "https://granta.com/products/granta-160-conflict/",
    "https://granta.com/products/granta-159-what-do-you-see/",
    "https://granta.com/products/granta-158-in-the-family/",
    "https://granta.com/products/granta-157-should-we-have-stayed-at-home-new-travel-writing/",
    "https://granta.com/products/granta-156-interiors/",
    "https://granta.com/products/granta-155-best-of-young-spanish-language-novelists-2/",
]

# URLs to exclude from piece detection
EXCLUDE_SLUGS = {
    'contributor', 'explore', 'products', 'wp-content', 'search', 'donate',
    'forgot-password', 'workshops', 'sales-and-distribution', 'prizes',
    'international-editions', 'grantas-environmental-policy', 'magazine-masthead',
    'xmlrpc', 'subscriptions', 'subscribe', 'about', 'authors', 'catalogue',
    'issues', 'advertise', 'acknowledgements', 'cookie-policy', 'contact-us',
    'jobs', 'merchandise', 'privacy-statement', 'rights', 'submissions',
    'team', 'terms', 'litbreaker', 'cart', 'books', 'courses', 'podcasts',
    'granta-com', 'always-late',  # nav/footer piece
}

def fetch(url):
    result = subprocess.run(
        ["curl", "-sL", url, "-A", HEADERS,
         "-H", "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
         "-H", "Accept-Language: en-US,en;q=0.9"],
        capture_output=True, text=True, timeout=30
    )
    return result.stdout

def strip_tags(html):
    return re.sub(r'<[^>]+>', '', html)

def decode_entities(text):
    return (text
        .replace('&amp;', '&').replace('&nbsp;', ' ').replace('&#038;', '&')
        .replace('&#8217;', "\u2019").replace('&#8216;', "\u2018")
        .replace('&#8220;', "\u201c").replace('&#8221;', "\u201d")
        .replace('&quot;', '"').replace('&lt;', '<').replace('&gt;', '>')
        .replace('&#8230;', '…').replace('&#8211;', '–').replace('&#8212;', '—')
    )

TYPE_MAP = {
    "essays & memoir": "Essay",
    "essays and memoir": "Essay",
    "fiction": "Fiction",
    "poetry": "Poetry",
    "in conversation": "Interview",
    "interview": "Interview",
    "art & photography": "Art & Photography",
    "art and photography": "Art & Photography",
    "reporting": "Reporting",
    "new writing": "New Writing",
    "memoir": "Essay",
    "essay": "Essay",
    "non-fiction": "Essay",
}

def is_excluded_url(url):
    path = url.replace('https://granta.com/', '').rstrip('/')
    slug = path.split('/')[0]
    return slug in EXCLUDE_SLUGS

def parse_issue(url, html):
    issue_num_match = re.search(r'/granta-(\d+)-', url)
    issue_number = int(issue_num_match.group(1)) if issue_num_match else None

    # Issue label: look for <title> or og:title
    og_title = re.search(r'<meta property="og:title" content="([^"]+)"', html)
    if og_title:
        issue_label = decode_entities(og_title.group(1)).strip()
        # Remove site name suffix if present
        issue_label = re.sub(r'\s*[\|–—-]\s*Granta.*$', '', issue_label).strip()
    else:
        issue_label = f"Granta {issue_number}"

    # Issue date: season + year pattern anywhere in html near the issue header
    # Look specifically in the product header area
    header_area = html[:html.find('single-contributor_related-wrapper') + 1] if 'single-contributor_related-wrapper' in html else html[:5000]
    date_match = re.search(
        r'((?:Winter|Spring|Summer|Autumn|Fall)\s+\d{4})',
        header_area
    )
    issue_date = date_match.group(1) if date_match else ""

    # --- Split into piece blocks ---
    # Each block is wrapped in: <div class="single-contributor_related-row_container">
    #   <div class="row single-contributor_related-wrapper"> ... </div>
    # We split on the outer container
    blocks = re.split(r'<div class="single-contributor_related-row_container">', html)

    pieces = []
    seen_urls = set()

    for block in blocks[1:]:  # skip everything before first block
        # Determine edition label from the desktop h6 header.
        # Header format: "<type> | <edition>" where edition is either
        # "The Online Edition" or "Granta N" (print).
        # A piece is PAYWALLED if it has the padlock icon class AND is NOT
        # in the Online Edition section. We verify by checking for the
        # padlock class — if present on a print block, skip it.

        desktop_h6 = re.search(
            r'single-contributor_related_header-text-desktop">(.*?)</h6>',
            block, re.DOTALL
        )

        if not desktop_h6:
            continue

        header_text = desktop_h6.group(1)
        is_online_edition = bool(re.search(r'The Online Edition', header_text))

        # The padlock <span> appears on all print pieces, but only truly
        # paywalled ones have a <img> (the closed lock icon) inside it.
        # Crucially the <img> lives in the MOBILE h6, not the desktop one —
        # so we search the full block, not just header_text.
        padlock_span = re.search(
            r'class="single-contributor_related_header-padlock">(.*?)</span>',
            block, re.DOTALL
        )
        is_paywalled = bool(padlock_span and '<img' in padlock_span.group(1))

        if is_paywalled:
            continue  # truly paywalled — skip

        # Edition label for the piece record
        edition = 'Online Edition' if is_online_edition else 'Print'

        # --- Content type ---
        type_match = re.search(
            r'class="single-contributor_related-red_text">(.*?)</span>',
            header_text
        )
        raw_type = decode_entities(strip_tags(type_match.group(1))).strip() if type_match else ""
        content_type = TYPE_MAP.get(raw_type.lower(), raw_type)

        # --- Piece URL + title from aria-label ---
        # <a href="https://granta.com/SLUG/" aria-label="Title">
        url_title_match = re.search(
            r'href="(https://granta\.com/([^"]+)/)"[^>]*aria-label="([^"]+)"',
            block
        )
        if url_title_match:
            piece_url = url_title_match.group(1)
            piece_title = decode_entities(url_title_match.group(3)).strip()
        else:
            # Fallback: find any granta.com piece URL in the block
            url_match = re.search(r'href="(https://granta\.com/([a-z][a-z0-9\-]+)/)"', block)
            if not url_match:
                continue
            piece_url = url_match.group(1)
            piece_title = ""

        if is_excluded_url(piece_url):
            continue

        # --- Title fallback: h1 inside right content ---
        if not piece_title:
            title_match = re.search(
                r'class="single-contributor_related-header">(.*?)</h1>',
                block, re.DOTALL
            )
            piece_title = decode_entities(strip_tags(title_match.group(1))).strip() if title_match else ""

        # --- Author ---
        author_match = re.search(
            r'href="https://granta\.com/contributor/[^"]+/"[^>]*>([^<]+)</a>',
            block
        )
        author = decode_entities(author_match.group(1)).strip() if author_match else ""

        if piece_url in seen_urls:
            continue
        seen_urls.add(piece_url)

        pieces.append({
            "title": piece_title,
            "url": piece_url,
            "author": author,
            "type": content_type,
            "edition": edition,
        })

    return {
        "issue_url": url,
        "issue_label": issue_label,
        "issue_number": issue_number,
        "issue_date": issue_date,
        "piece_count": len(pieces),
        "pieces": pieces,
    }


def main():
    issues = []
    total_pieces = 0

    for issue_url in ISSUE_URLS:
        print(f"Fetching {issue_url} ...", end=" ", flush=True)
        html = fetch(issue_url)
        if not html or len(html) < 5000:
            print("FAILED")
            continue

        issue = parse_issue(issue_url, html)
        issues.append(issue)
        total_pieces += issue["piece_count"]
        print(f"{issue['issue_label']} | {issue['issue_date']} | {issue['piece_count']} free pieces")
        time.sleep(0.3)

    output = {
        "source": "https://granta.com/issues/",
        "total_issues": len(issues),
        "total_pieces": total_pieces,
        "issues": issues,
    }

    out_path = "/home/user/workspace/granta_issues.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n✓ {len(issues)} issues, {total_pieces} free pieces")
    print(f"✓ Saved to {out_path}")


if __name__ == "__main__":
    main()
