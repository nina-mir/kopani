# Progress Report — SQLite ↔ Astro Integration (Card UI Testing)

**Date:** 2026-05-24
**Goal:** Wire `kopani.sqlite` into the Astro frontend and render 50 real pieces on `index.astro` to stress-test `Card.improved.astro` against real data.

## What was done

Connected `better-sqlite3` to the Astro build and replaced the temporary `stories` placeholder array in `index.astro` with a live, stratified-random sample of 50 pieces drawn from the database. Status: **working in dev.**

### `src/lib/db.ts`
- Added `getRandomPieceCards(total = 50)`, which returns objects already mapped to the Card's `PieceCard` shape — so `index.astro` stays a one-liner and all DB→UI mapping lives in one place.
- **Stratified random sampling** rather than pure `RANDOM()`. Pieces are bucketed into four groups — has translator + visual artist (both), translator-only, visual-only, neither — and the sample is filled by quota (`both 10 / tr 10 / va 12 / neither 18`), then topped up at random and shuffled. This guarantees every Card variant renders on each build, instead of relying on luck (translators ≈ 7% and visual artists ≈ 17% of pieces, so a pure random 50 could easily show zero of a rare variant).
- The quota block is the single tuning knob if we want to hammer rarer variants harder.
- No `ingestion_status` filter, per decision — any 50 pieces, every build. Filtering is deferred to a later stage.

### `src/pages/index.astro`
- Deleted the temporary `stories` array (the shape never matched `Card.improved`).
- Now: `const pieces = getRandomPieceCards(50)` → `{pieces.map((piece) => <Card piece={piece} />)}`. Editorial intro section kept as-is.

## Bugs hit and fixed
1. **`attempt to write a readonly database`** — caused by `db.pragma('journal_mode = WAL')`. WAL writes to the file header, which a `readonly` connection forbids. WAL is also pointless for a read-only build connection. **Removed the line.** (The integration guide's "safe for read-only too" comment is incorrect, at least on Windows.) Kept `foreign_keys = ON`.
2. **`db is not defined`** — the `const db = new Database(...)` line got clipped while editing out WAL, so the prepared statements had no `db` in scope. **Restored the connection line.**

## Known behavior — data, not bugs
- **Most cards show the hatched fallback texture, not a photo.** `image_url` (Kopani-owned) is essentially all NULL, and `source_image_url` is intentionally not displayed. The Card's `<img>` branch is not exercised by real data yet — hardcode an `imageUrl` on one card to test it.
- **Many deks are empty.** `summary` is unpopulated; `meta_description` exists only for some journals (Evergreen yes, Threepenny no). Good for testing the no-dek layout.
- **Layout shifts between builds** because the sample reshuffles each time — useful for surfacing long titles / missing contributors, but means a glitch may not reproduce on the next build.

## Open items for Card refinement
- Verify `@theme` defines every custom token the Card uses: `bg-linen`, `text-prussian`, `text-ochre`, `text-umber`, `text-earth-bron`, `font-arno`, `font-card-title`, `font-secret-service`, etc. Undefined tokens fail silently and look like layout bugs.
- **Typo in `Card.improved.astro`:** `font--secret-service` (double dash).
- `min-h-[92vh]` makes each card nearly full-screen tall — 50 of them is a very long page.
- Author route currently points at `/authors/{slug}` (these pages don't exist yet; fine for now).

## Decisions on record
No status filtering yet · featured ignored for now · contentType left lowercase in data (uppercased by CSS) · author route deferred · stratified random chosen over pure random.
