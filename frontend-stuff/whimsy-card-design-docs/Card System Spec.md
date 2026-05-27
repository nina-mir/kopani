# Kopani — Card System Spec v1

A design specification for the six card injections from `Card Whimsy.html`.
Companion file, not implementation. Use alongside the visual reference.

---

## 0 · Shared foundation

Every card keeps the existing **mcard** anatomy:
cover (460px tall) · kicker block (top-left) · `read` button (top-right) ·
title plate (bottom-left) · body (dek · rule · meta · byline · tags).

### Tokens

| Token | Value | Used for |
|---|---|---|
| `cream` | `#f5ede0` | card background |
| `cream-soft` | `#efe5d2` | tag chips |
| `cream-line` | `#d8c8ac` | hairlines |
| `blue` | `#2c3e6b` | kicker, stamp border |
| `ochre` | `#8b6914` | source name, dividers |
| `brick` | `#c0392b` | the accent — tape, seal, marginalia, gauge fill |
| `umber` | `#3d2b1f` | meta type |
| `ink` | `#1c1208` | titles, body |
| `plate` | `#1f1a13` | title-plate background |

### Type

- **Display** — Cormorant Garamond · titles, source name (italic)
- **Body** — IM Fell English · dek, byline
- **Mono** — Courier Prime · kicker, meta, all artifact labels
- **Hand** — Caveat · marginalia only

### Visual grammar of an "injection"

Every injection must satisfy at least three of:
1. Mono type or hand type (never display).
2. Brick-red accent somewhere.
3. A paper-artifact metaphor (tape, seal, slip, stamp, tab, spine).
4. A small rotation (±2°–7°) or a tactile shadow.
5. Communicates curatorial intent, not decoration.

---

## 1 · Hatch-by-genre  *(systemic — applies to all cards)*

The cover texture changes by content type. Same gradient, same vignette,
same opacity — only the hatch direction/shape differs.

| Genre | Hatch |
|---|---|
| Fiction | diagonal 135°, 6px stripe |
| Nonfiction | horizontal rules, 9px |
| Poetry | wide verticals, 14px |
| Interview | crosshatch (45° + 135°), 7px |
| Translation | mirrored diagonal, 6px |
| Art | halftone dots, 8px grid |

Hatch opacity: `rgba(28,18,8,0.13–0.18)`. Never louder than that —
it's a watermark, not pattern.

---

## 2 · Library slip

A small ex-libris card "taped" to the lower-right of the cover.

- **Size:** 156 × ~90 px (auto height by content)
- **Position:** bottom-right of cover, 18 / 22 px inset
- **Rotation:** −1.8°
- **Background:** cream `#f5ede0`, 1px umber border, drop-shadow 1px
- **Tape strip:** 36 × 14 px, hatched brick (same as `read` button), tilted −3°, sits at top edge
- **Type:** Mono 9.5px body, 8.5px caps headings
- **Content:** `gathered` (date) · `shelf` (issue + code) · `borrowed` (status). Always 3 rows.

**When to use:** any card. Carries curatorial provenance.

---

## 3 · Editor's seal

A circular wax-stamp medallion in the upper-left of the cover.

- **Size:** 92 × 92 px circle
- **Position:** top-left, 18 / 18 px inset; pushes kicker block to `left: 130px`
- **Rotation:** −7°
- **Fill:** brick gradient with inner light/shadow + double inner ring (cream → brick)
- **Type:** Mono 9px caps, white-cream on brick
- **Content:** glyph (✶) · two short lines (e.g. "Editor's Choice")

**When to use:** scarce — roughly **1 in 5–6 cards**. Scarcity is the point.

---

## 4 · Marginalia note

A handwritten editor's note over the cover, near the title plate.

- **Position:** bottom-right of cover, above tags zone
- **Rotation:** −4°
- **Type:** Caveat 22px, brick `#c0392b`
- **Max width:** ~200 px
- **Signature:** 15px, brick @ 75% opacity, single initial (e.g. "— m.")
- **Underline:** 60% width, 1.5px brick, tilted −2°, beneath signature
- **Voice:** ≤ 8 words. Imperative, intimate. ("read aloud, slow.")

**When to use:** ~1 in 8 cards. Reserved for genuine editor favourites.
Never on cards that also carry a seal — too loud together.

---

## 5 · Read-time gauge  *(replaces "X min read" in meta row)*

A typewriter-feel horizontal gauge that replaces the read-time text.

- **Track:** 72 × 7 px, double horizontal rule (top & bottom umber)
- **Ticks:** 4 internal verticals at 20/40/60/80% — represent 5/10/15/20 min
- **Fill:** brick hatched stripe, height `track − 2px`
- **Dot:** 9 × 9 px brick circle with umber border, centred on fill end
- **Labels:** mono 10.5px `read` (left), mono 8.5px `18 min · long` (right)
- **Scale:** 0 / 5 / 10 / 15 / 20+ min

**When to use:** systemic — replace every meta-row "min read" with the gauge
once adopted. Looks like a colophon instrument.

---

## 6 · Spine + index tab

The card becomes a journal on a shelf: a coloured spine on the left edge,
plus a Filofax-style index tab protruding from the upper-left.

- **Spine:** 14 px wide, full card height (top → bottom)
  - Colour by genre: fiction = brick · nonfiction = blue · poetry = ochre · interview = umber
  - Vertical mono label, 9px caps, cream text (e.g. "Interview · S/S '25")
- **Tab:** rectangular, protrudes left of spine
  - Position: top of cover area, ~28 px down
  - Padding: 5/10/5/18 px; cream fill, 1px umber border (no left border)
  - Type: Mono 9.5px caps, ink
  - Shadow: 1px hard offset
- **Card adjustment:** card padded `left: 14px` to accommodate spine

**When to use:** systemic alternative to the kicker block when you want the
genre to be the loudest signal. Pairs well with hatch-by-genre.

---

## 7 · Issue stamp

A rubber-stamped date block sitting between the kicker and the `read` button.

- **Size:** auto · roughly 80 × 36 px
- **Position:** top of cover, `right: 92px` (left of `read`)
- **Rotation:** −4°
- **Border:** 2px blue `#2c3e6b`, no fill (faint cream tint)
- **Type:** Mono 9.5px caps blue, 7.5px caps subline blue @ 80%
- **Content:** `Received` / `S/S · 2025` (or similar process verb + date)

**When to use:** any card. Especially good on translations, reprints, late
additions — anywhere the card represents an *acquisition event*.

---

## Grid orchestration

Treat the six injections as voices in a chorus, not a checklist.

### Per-card cadence
- **1 injection** = ideal
- **2 injections** = allowed
- **3+** = no

### Per-row of three
- At least one card should differ from the others by injection
- Never repeat the same artifact in adjacent cards
- Don't put a seal and marginalia in the same row

### Site-wide frequency (per 12 cards)
| Injection | Cadence |
|---|---|
| Hatch-by-genre | **all 12** |
| Read-time gauge | **all 12** (replaces text) |
| Spine + tab | 4–6 |
| Library slip | 4–6 |
| Issue stamp | 2–4 |
| Editor's seal | 1–2 |
| Marginalia note | 1–2 |

### Pairing rules
- ✅ Spine + Gauge · Slip + Gauge · Hatch + anything · Stamp + Slip
- ✅ Seal + plain card (let the seal breathe)
- ❌ Seal + Marginalia
- ❌ Slip + Marginalia (both occupy the lower-right)
- ❌ Stamp + Seal (both compete near the top)

### Mobile (single-column stack)
Variety matters *more*, not less. Alternate injections down the scroll —
don't let two consecutive cards carry the same artifact. Spine + tab is
particularly strong on mobile because it reads as a real shelf.

---

## Decision flow when assigning a card

1. **Genre** → sets hatch + spine colour (automatic, no choice).
2. **Editorial weight** → editor's pick? → seal *or* marginalia (not both).
3. **Provenance worth surfacing?** → slip (if curatorial) or stamp (if acquisition).
4. **Always** → gauge replaces read-time.
5. **Default** → just hatch + gauge. A "plain" card is essential to the rhythm.

A grid where every card is loud is the same problem you started with,
inverted. Silence between artifacts is what makes them feel chosen.
