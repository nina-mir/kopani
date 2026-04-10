# Kopani MVP Roadmap

## Product premise

Kopani is a reader-facing discovery platform for independent literary journals. Its first job is not to become a full ecosystem for writers, journals, and submissions; its first job is to prove that a one-person team can reliably surface strong work from small journals, package it beautifully, and drive readers back to the original publications. The MVP should therefore optimize for three measurable outcomes: publishable content density, repeatable editorial workflow, and outbound click-through to partner journals.

## MVP goal

The MVP should answer one core question:

**Can a single founder build a beautiful literary front page that aggregates and curates work from independent journals, updates it regularly, and generates enough reader engagement and journal interest to justify further development?**

Everything in the MVP should support one or more of these validation targets:

- Readers can discover work quickly.
- The site looks editorially credible and worth returning to.
- The platform can ingest literary-journal content with a repeatable workflow.
- Journal links receive meaningful outbound traffic.
- The founder can maintain the system alone for at least several weeks.

## What the MVP is

The MVP is a **curated literary discovery front page plus a lightweight content pipeline**.

It includes:

- A polished homepage.
- A small but high-quality database of journals and pieces.
- A repeatable scraping and metadata-normalization workflow.
- Basic categorization and editorial curation.
- Outbound linking to the original journals.
- Newsletter capture and analytics.

It does **not** need to include the full future vision, such as:

- Writer accounts.
- Submission tracking.
- AI recommendation engine.
- Full-text search over all scraped works.
- Journal dashboards.
- Payments marketplace.
- Community features.

Those are later-phase ideas.

## MVP scope

### Core content scope

Start narrow. Do not scrape the entire literary internet immediately.

Recommended launch dataset:

- 10 to 20 literary journals.
- 300 to 1,000 works total.
- Focus on prose, poetry, essays, interviews, and reviews only if easy to identify.
- Prefer journals with stable archives and clean public URLs.
- Prioritize active journals with recognizable reputations and readable web layouts.

Good initial data goals:

- 10 journals fully profiled.
- 50 to 100 standout pieces manually featured.
- 300+ additional pieces ingested into a hidden or browseable catalog.

### Recommended journal tiers

#### Tier 1: easiest launch journals

Pick journals with relatively straightforward archive structures and recent web publishing habits.

- New Orleans Review
- Evergreen Review
- Virginia Quarterly Review
- Ploughshares

#### Tier 2: selective additions after workflow stabilizes

- Paris Review
- London Review of Books
- New York Review of Books

These bigger brands may be more complex and can wait until the pipeline is reliable.

## Primary users for the MVP

### Reader

The MVP reader is someone who:

- Likes literature but does not track many journals.
- Wants quick discovery of poems, stories, and essays.
- Likes editorial framing such as “3 poems worth your morning.”
- Is willing to click out to read on the original journal site.

### Journal editor or staff member

This secondary user wants:

- More traffic.
- More visibility.
- Beautiful external coverage.
- Confidence that Kopani is additive rather than extractive.

### Founder-operator

This is critical. The system must be maintainable by one person.

The founder needs:

- A manageable ingestion workflow.
- Simple editorial tooling.
- Basic analytics.
- Minimal production overhead.

## MVP feature set

### Must-have features

#### 1. Homepage

The homepage is the product. It should look like a real editorial destination, not a search interface.

Requirements:

- Hero area with top featured story/package.
- Multiple curated rails or sections.
- Editorial cards with title, journal, author, type, short dek, and outbound link.
- Visual hierarchy strong enough to make readers browse naturally.
- Mobile-responsive design.
- Fast load speed.

Suggested sections:

- Editor’s Picks
- New This Week
- Poems
- Stories
- Essays
- Interviews
- From Small Journals
- Browse by Journal

#### 2. Journal profile pages

Each journal should have a simple profile page.

Fields:

- Journal name
- Description
- URL
- Genres covered
- Location, if relevant
- Publishing frequency, if known
- Recent pieces included on Kopani

#### 3. Piece cards and piece pages

You have two options:

- **Option A:** Card-only system, where every item links straight to the original source.
- **Option B:** Lightweight internal piece page with a short original blurb plus metadata and an outbound CTA.

For a one-person MVP, **Option B is usually better** because it gives you SEO surface area, stronger editorial voice, and a place to standardize metadata.

Internal piece page should include:

- Title
- Author
- Journal
- Genre/type
- Short original summary or blurb
- Tags/themes
- Publication date if available
- Read-time estimate if you can calculate it
- Large CTA: “Read the original at [Journal]”

Important rule:

- Do not republish copyrighted full text without permission.
- Use short original summaries and outbound links.

#### 4. Categorization and taxonomy

You need a minimal taxonomy that supports browsing without creating maintenance chaos.

Use only a few controlled fields at launch:

- Content type: poem, fiction, essay, interview, review, hybrid
- Length: short, medium, long
- Tone: lyrical, strange, political, funny, intimate, experimental, etc. (optional at launch)
- Themes: grief, desire, migration, labor, memory, family, city, body, war, faith, class, etc.
- Journal

- Do not create 100 tags. Start with:

    - 6 content types  (e.g., poem, story, essay, interview, review, hybrid)

    - 10 to 20 themes max (e.g., grief, migration, city, war, etc.)

    - 5 to 10 editorial collections (hand-curated groupings like “Small Journals,” “Queer Futures,” “Short & Strange”)

#### 5. Search and browse

Keep this simple.

MVP search requirements:

- Search by title, author, journal
- Filter by content type
- Filter by journal
- Filter by theme if implemented

If search is too heavy initially, launch with browse pages first.

#### 6. Newsletter signup

This is essential.

Requirements:

- Email capture in homepage hero and footer
- Minimal promise statement, e.g. “The best new work from independent literary journals, weekly.”
- Integration with a simple newsletter tool

#### 7. Analytics

You need to know whether the product works.

Track:

- Page views
- Unique users
- Newsletter signups
- Outbound clicks by piece
- Outbound clicks by journal
- Top content categories
- Returning visitors if possible

### Nice-to-have features

These are helpful but should not block launch.

- Saved reading list
- Personalized home feed
- AI-generated similarity recommendations
- Submission calendar
- Journal ranking pages
- Author pages
- Social sharing cards per piece
- “Read next” recommendation module

## Data and content pipeline

This is the real backbone of the MVP.

### Data model

You should define three core entities:

#### Journal

Fields:

- `id`
- `name`
- `slug`
- `homepage_url`
- `description`
- `country`
- `city`
- `genres_supported`
- `status`
- `notes`

#### Piece

Fields:

- `id`
- `title`
- `slug`
- `original_url`
- `journal_id`
- `author_name`
- `content_type`
- `summary`
- `publication_date`
- `issue_title` or `issue_number`
- `themes`
- `estimated_read_time`
- `word_count_estimate`
- `featured` boolean
- `image_url` https://kopani.ai/assets/pieces/new-orleans-review-123.jpg
- `source_image_url` : https://journal-site.org/uploads/header-image.jpg
- `image_alt`
- `image_rights_status`:  owned / licensed / partner-approved / do-not-display
- `image_credit`: Courtesy of New Orleans Review
- `source_status` (scraped, reviewed, published)

#### Editorial collection

Fields:

- `id`
- `title`
- `slug`
- `description`
- `items`
- `display_order`

### Ingestion pipeline stages

#### Stage 1: discover source structure

For each journal:

- Identify archive structure.
- Identify whether pieces live on individual pages.
- Identify author pages, issue pages, tag pages, and pagination.
- Decide whether the journal is scrapeable without browser automation.

Deliverable:

- One source profile file per journal.

#### Stage 2: scrape metadata

Extract:

- Title
- URL
- Author
- Publication date if present
- Journal name
- Category if present
- Short excerpt if legally safe and technically easy

Deliverable:

- Structured JSON or CSV per journal.

#### Stage 3: normalize

Map each journal’s raw fields into a common schema.

Examples:

- “Poetry” and “Poem” both become `poem`
- “Creative Nonfiction” becomes `essay` or `nonfiction`
- Missing dates become null, not fake values

Deliverable:

- Clean normalized table of pieces.

#### Stage 4: enrich

Add:

- Themes
- Read-time estimate
- Internal summary/dek
- Featured/not featured
- Quality review notes

This enrichment can be partially manual early on.

#### Stage 5: publish

Push approved records into the site’s public database or CMS.

## Recommended implementation strategy

### Editorial strategy: hybrid automation

Do not fully automate the front page. Fully automated literary curation will feel flat and messy.

Use a hybrid workflow:

- Scraping and metadata extraction: automated
- Taxonomy suggestions: semi-automated
- Final homepage placement and blurbs: manual

That is the right balance for a one-person literary startup.

### Technical architecture

Keep the stack boring and maintainable.

Suggested setup:

- Frontend: Next.js, Astro, or a simple React framework with static generation
- Database: Supabase or PostgreSQL
- Scraping: Python with requests + BeautifulSoup; Playwright only when necessary
- Storage: local + cloud bucket for structured exports
- CMS/admin: simple internal admin panel or direct database table editing
- Analytics: Plausible, PostHog, or GA4
- Newsletter: beehiiv, ConvertKit, or Buttondown
- Hosting: Vercel, Netlify, or Cloudflare Pages

### Why this stack works for one person

- Easy deploys
- Strong developer ergonomics
- Cheap at small scale
- Good enough for SEO and editorial content
- Does not force you into enterprise complexity

## Visual and editorial requirements

Kopani’s front page must feel genuinely desirable. If the design looks generic, readers will not trust the curation.

### Design principles

- Magazine feel, not database feel
- Minimal but rich typography
- Strong hierarchy
- Fast scanning
- Warm, literary tone
- Mobile first but desktop elegant

### Content voice

Avoid academic or overly precious language.

The tone should be:

- intelligent
- warm
- slightly mischievous
- selective
- confident

Example blurbs:

- “A grief essay that moves like a confession and lands like a warning.”
- “Three poems that make the ordinary feel briefly radioactive.”
- “A short story that starts domestic and ends feral.”

## MVP phases

## Phase 0: setup and decisions

Duration: 2 to 4 days

Deliverables:

- Brand locked: Kopani
- Domain and hosting chosen
- Stack chosen
- Source journal shortlist finalized
- Data schema finalized
- Legal/editorial policy drafted

Tasks:

- Register domain
- Set up repo
- Set up database
- Create journal target list
- Define metadata schema
- Write basic scraping ethics policy and copyright rules

## Phase 1: ingestion prototype

Duration: 4 to 7 days

Goal:

- Prove you can scrape and normalize 3 to 5 journals consistently.

Deliverables:

- Source profile docs for first journals
- Working scraper scripts
- Clean dataset of at least 100 to 300 pieces
- One enrichment workflow

Tasks:

- Build source-specific scrapers
- Normalize into common schema
- Manually review results
- Add first taxonomy rules

Success criteria:

- At least 80 percent of key fields extracted correctly
- No catastrophic duplication
- Stable reruns possible

## Phase 2: editorial database and curation layer

Duration: 3 to 5 days

Goal:

- Turn raw scraped data into publishable content.

Deliverables:

- Admin method for marking pieces as featured
- Summary/dek workflow
- Homepage section definitions
- First 50 curated items

Tasks:

- Create editorial status field
- Add feature flags
- Create collection logic
- Write blurbs for first homepage batches

Success criteria:

- You can select, summarize, and publish without touching raw code too much

## Phase 3: frontend MVP

Duration: 5 to 8 days

Goal:

- Launch a beautiful, usable public site.

Deliverables:

- Homepage
- Journal pages
- Piece pages or outbound cards
- Basic search/browse
- Newsletter signup
- Analytics

Tasks:

- Build homepage sections
- Build journal and piece templates
- Style cards and responsive layouts
- Add outbound click tracking
- Set up metadata and SEO basics

Success criteria:

- Site feels polished enough to show publicly
- Readers can browse and click easily
- It works on mobile

## Phase 4: launch readiness

Duration: 2 to 4 days

Goal:

- Make the MVP safe and credible to show.

Deliverables:

- About page
- Submission/partnership page for journals
- Privacy policy
- Copyright/contact policy
- QA checklist completed

Tasks:

- Add attribution language
- Add journal contact option
- Test all outbound links
- Remove broken or weak content
- Proofread all homepage copy

Success criteria:

- You can send the site to editors without embarrassment

## Total realistic MVP timeline

For one person working intensely:

- Fast sprint: 2 to 4 weeks
- More realistic: 4 to 6 weeks

Do not let the MVP expand past this.

## Feature prioritization matrix

| Feature | Launch now | Later | Reason |
|---|---|---|---|
| Beautiful homepage | Yes |  | Core product |
| Journal profile pages | Yes |  | Supports credibility and browsing |
| Piece pages with blurbs | Yes |  | Strong editorial layer |
| Outbound click tracking | Yes |  | Core validation metric |
| Newsletter signup | Yes |  | Retention and monetization path |
| Search by title/author/journal | Yes |  | Basic discoverability |
| AI recommendations |  | Later | Nice but unnecessary at launch |
| Writer accounts |  | Later | Not needed to validate reader demand |
| Submission tracker |  | Later | Separate product surface |
| Journal dashboards |  | Later | Good for monetization later |
| User comments/community |  | Later | High moderation burden |

## Non-functional requirements

These matter just as much as features.

### Performance

- Homepage should load quickly.
- Images should be optimized.
- Mobile performance should be strong.

### Reliability

- Scrapers should fail gracefully.
- Broken source pages should not break the site.
- You should be able to rerun ingestion without duplicating data.

### Legal and ethical safety

- Do not republish full text without permission.
- Attribute clearly.
- Link to original source prominently.
- Honor takedown requests.
- Check robots.txt and avoid abusive scraping.

### Editorial quality

- Every featured item should feel hand-selected.
- Summaries should be original, short, and accurate.
- Taxonomy should remain clean and consistent.

## Operating workflow for a one-person team

### Weekly workflow after launch

#### 1. Source refresh

- Run scrapers for active journals.
- Review new candidates.
- Remove bad records.

#### 2. Curate

- Select 10 to 20 pieces.
- Write short blurbs.
- Update homepage rails.

#### 3. Publish newsletter

- Package best pieces of the week.
- Link back into Kopani and out to journals.

#### 4. Measure

- Review top click-throughs.
- Track journal traffic sent.
- Note which sections perform best.

#### 5. Outreach

- Send partner updates to journals.
- Ask for quotes/testimonials.
- Invite journals to share their profile pages.

## Success metrics for the MVP

You need clear indicators that the MVP is working.

### Product metrics

- Number of journals onboarded
- Number of pieces ingested
- Number of curated pieces published
- Homepage CTR to external journals
- Newsletter signup conversion rate
- Returning visitor rate

### Business validation metrics

- Number of journal editors who respond positively
- Number of journals willing to be featured
- Number of journals that share Kopani links
- Number of sponsorship or partnership conversations started

### Founder-operations metrics

- Hours needed per weekly refresh cycle
- Time required to onboard a new journal
- Ratio of manual cleanup to useful output

## Risks and how to reduce them

| Risk | Why it matters | Mitigation |
|---|---|---|
| Scraping complexity explodes | One founder gets buried in edge cases | Start with a small journal set and stable source patterns |
| Taxonomy becomes chaotic | Browsing quality degrades | Keep a small controlled vocabulary |
| Site looks too generic | Users do not trust curation | Invest heavily in homepage design and editorial tone |
| Copyright concerns | Potential reputational or legal problem | Use summaries, attribution, and strong outbound CTAs |
| No repeat usage | Discovery site feels one-off | Build newsletter and recurring weekly updates from day one |
| Too many features | Launch slips indefinitely | Separate launch-now vs later rigorously |

## Recommended launch checklist

Before launch, Kopani should have:

- A strong homepage with at least 30 to 50 excellent live pieces
- At least 8 to 10 journal pages
- Working outbound click tracking
- Working email signup
- Consistent branding and typography
- Clean mobile experience
- About/mission page
- Contact/takedown policy
- At least one week of planned editorial content after launch

## Best immediate next steps

1. Lock the first 10 journals.
2. Design the exact metadata schema.
3. Build one scraper end to end for a simple journal.
4. Decide whether launch uses internal piece pages or direct outbound cards.
5. Build homepage first, then ingestion around it.
6. Manually curate the first 30 to 50 pieces before trying to automate everything.

## Final recommendation

The best one-person MVP for Kopani is not “AI for all literary journals.” It is a **beautiful editorial site with a disciplined ingestion pipeline and enough structured data to update reliably**.

The winning wedge is:

- excellent taste
- clear metadata
- strong design
- respectful aggregation
- measurable traffic sent back to journals

If that works, everything else can come later.
