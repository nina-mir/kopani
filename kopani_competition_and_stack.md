     # Kopani – Startup Competition & Tech Stack Notes

## 1. Funding / competition context

### 1.1. Your constraint

- You **don’t have 12 months** to slowly build; you likely need **cash by month two**.
- You’re comfortable doing:
  - all the core product work,
  - all of the marketing,
  - and hustling for hackathons / competitions.
- So the goal is not a perfect product; it’s a **fast, credible proof-of-cash and proof-of-traction machine**.

### 1.2. What to optimize for

For the competition / early money, the MVP should optimize for:

- **Speed to a compelling demo** (for judges, angels, partners).
- **Evidence of real-world demand**:
  - recurring readers,
  - outbound clicks to journals,
  - newsletter subscribers,
  - interest from journals.
- **A believable, near-term revenue story**:
  - founding journal partner packages,
  - early newsletter sponsors,
  - small angel/bridge round.

You are not pitching “just another lit mag,” but:

> A front page and data platform that sends attention and traffic back to independent journals.

---

## 2. What will work in a startup competition context

### 2.1. Framing and narrative

Likely to resonate:

- **Sharp problem statement**:
  - Discovery for independent literary journals is broken.
  - Readers don’t know where to look.
  - Journals lack data and cross-journal discovery tools.
- **Clear value proposition**:
  - For readers: a single front page for high-quality work from many journals.
  - For journals: new traffic, visibility, and eventually analytics.
- **Concrete impact story**:
  - “In the last X weeks, we sent Y clicks to Z journals and grew a list of N readers.”

Good competition narrative:

- Kopani is **infrastructure for a fragile cultural ecosystem**, not just content.
- You are **aggregating and directing attention**, then plan to add tools (analytics, automation) on top.

### 2.2. Fast, realistic paths to cash

For both competitions and pre-seed investors, these are credible:

- **Founding journal partner packages**:
  - Feature slots, issue launch coverage, link tracking.
  - Low-price pilot (e.g., one-off fees) to prove willingness to pay.
- **Newsletter sponsorships**:
  - Even small but focused lists can sell ads if the audience is tight and high-intent.
- **Hackathon/competition prizes**:
  - Short, intense build → polished demo → prize money + visibility.
- **Tiny mission-aligned angel check**:
  - People who care about literary culture, publishing, or creator tools.

### 2.3. “Why this isn’t just a blog”

Key talking points:

- **Data + curation + workflow**, not just essays:
  - Structured metadata for pieces and journals.
  - Repeatable scraping and normalization.
  - Status-aware ingestion pipeline.
- **Two-sided value**:
  - Readers get discovery.
  - Journals get traffic and eventually insight.

---

## 3. What will *not* work (or is risky) at this stage

### 3.1. Over-building

Things that are dangerous for a 1–2 month timeline:

- Trying to ship:
  - full writer account system,
  - complex submission tracker,
  - personalized recommendation engine,
  - journal dashboards,
  - full community features.
- Over-modeling every possible metadata nuance (issues, formats, all edge-case journal structures).

### 3.2. Overly heavy branding choices

- Using names tied directly to:
  - Holocaust-era archives,
  - Warsaw Ghetto resistance,
  - or existing major English-language magazines.
- Reusing exact titles like **The Banner**, **The Contemporary**, **The Margins**, **Commonplace**, or **Anaphora** that are already taken in your niche.

You can be inspired by resistance and archival history as an **internal ethos**, but the brand itself should be more flexible and less loaded.

### 3.3. Copyright risk

For the MVP and competition:

- Do **not**:
  - scrape and republish full texts,
  - hotlink or embed third-party images without permission,
  - ship public datasets of scraped content.
- You should:
  - use **short original blurbs**,
  - clearly attribute journals,
  - link out to the original piece,
  - be prepared to honor takedown requests.

Competitions and early investors will be turned off by obvious IP risk.

---

## 4. MVP product wedge for the competition

### 4.1. Core demo

For a judge or investor looking at Kopani in a demo, the most impressive version is:

- A **live front page** (Kopani Post) that:
  - shows real pieces from multiple journals,
  - looks and feels like a serious magazine/portal,
  - is updated regularly.
- A **small but real catalog**:
  - 10–20 journals,
  - hundreds of pieces ingested,
  - dozens curated with blurbs.
- **Analytics story**:
  - tracked outbound clicks to journals,
  - basic usage numbers (page views, returning users).
- A sense of **pipeline and robustness**:
  - you can add a new journal and have content flowing within a predictable pipeline.

### 4.2. Business hooks

For the pitch and competition materials:

- “Founding Partner” concept:
  - A small first cohort of journals that get extra features and visibility.
- “First sponsor” story:
  - Example packages for MFA programs, small presses, residencies, or services that want to reach your audience.
- Clear statement of how this scales:
  - More journals → richer discovery,
  - More readers → more value for journals and sponsors,
  - Data layer → smarter tools and analytics over time.

---

## 5. Tech stack for the MVP (summary)

The agreed direction is **boring, stable, and one-person friendly**.

### 5.1. Database and data layer

- **SQLite** for the MVP:
  - Simple, file-based, no extra infra.
  - Good for local iteration and early production if traffic is modest.
- **Six tables**:
  - `journals`
  - `pieces`
  - `authors`
  - `piece_authors`
  - `themes`
  - `piece_themes`
- **Surrogate integer primary keys** on entity tables.
- **Composite primary keys** on junction tables.
- Enum-like fields implemented with `TEXT` + `CHECK` constraints.

The schema is designed to support:

- Many-to-many relationships (piece↔author, piece↔theme).
- Clean joins and future migration to Postgres if needed.

### 5.2. Scraping and ingestion

Suggested approach:

- **Language**: Python (requests + BeautifulSoup) or similar.
- **Per-journal “source profiles”**:
  - archive URL structure,
  - selectors for title, author, date, etc.,
  - pagination patterns,
  - known quirks.
- **Pipeline stages** (tracked via `ingestion_status`):
  - `discovered` → `scraped` → `normalized` → `needs_review` → `ready` → `published` / `rejected` / `error`.

Data model is organized into:

- Raw (transient scraping output),
- Normalized (Kopani schema),
- Published (only what is allowed/desired for the live site).

### 5.3. Application / frontend

You haven’t locked in a specific framework in this thread, but the general principles:

- Choose a **modern JS framework** that supports:
  - server-side rendering / static generation,
  - simple routing,
  - easy deployment (e.g., Vercel/Netlify/Cloudflare if you choose later).
- Focus on:
  - A **hero + sections** layout for the homepage.
  - Journal and piece pages that are **clean and responsive**.
- Keep dependencies small.

Candidates (not formally chosen here, but consistent with the plan):

- React-based meta-framework (Next.js, Astro, etc.) or similar.

### 5.4. Analytics and newsletter

Recommended:

- Lightweight analytics (Plausible, PostHog, or similar) to track:
  - page views,
  - outbound clicks per piece/journal,
  - basic engagement.
- A **newsletter tool** for:
  - weekly highlights,
  - early sponsorship experiments.

---

## 6. Tactical sequence for you

Based on this thread, a practical order of work:

1. **Lock schema** in SQLite (the 6 tables + indexes).
2. **Implement ingestion** for 3–5 pilot journals:
   - source profiles,
   - scrape → normalize → store.
3. **Build the admin/curation flow**:
   - mark pieces as `featured`,
   - write summaries,
   - assign themes.
4. **Build Kopani Post homepage**:
   - use curated pieces to populate sections.
5. **Add analytics and basic email capture**.
6. **Polish pitch materials** for the competition:
   - problem + solution,
   - demo walkthrough,
   - early numbers (even if small),
   - near-term revenue experiments.

This aligns all the earlier conversation into a single, consistent plan you can point to as you work.