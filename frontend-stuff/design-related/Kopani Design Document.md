# Kopani — Design Document
*Version 1.0 · April 2026*

---

## Concept

Kopani is a literary aggregator — a front page that links to poems, fiction, essays, interviews, and art pieces published on independent literary journals (Paris Review, Granta, Evergreen Review, Ploughshares, etc.). The editorial model is analogous to HuffPost for the independent literary press: one destination that surfaces the best work from many sources.

---

## Aesthetic Direction

### Concept Reference
The visual language is rooted in **1880 Amsterdam** — the era of Dutch broadsheet printing, canal-house interiors, and the warm, muted palette of Northern European oil painting. The goal is gravitas without stiffness: a platform that feels like a physical object worth picking up.

### Color Palette

| Role | Name | Value |
|---|---|---|
| Background | Aged Linen Cream | `#f5ede0` |
| Secondary BG / borders | Cream Dark | `#e0d0b8` |
| Primary accent | Prussian Blue | `#2c3e6b` |
| Secondary accent | Burnt Ochre | `#8b6914` |
| Alert / kicker | Brick Red | `#c0392b` |
| Deep tone | Umber | `#3d2b1f` |
| Body text | Ink | `#1c1208` |

### Typography

| Role | Family | Weight / Style |
|---|---|---|
| Display / headlines | Cormorant Garamond | 300–600; italic for hero titles |
| Body / bylines / nav | IM Fell English | Regular; italic for deks and meta |

Both families are loaded from Google Fonts. Together they echo the New Yorker's Caslon-derived tradition while carrying a stronger old-world, letterpress quality. Cormorant Garamond is used exclusively for headlines to preserve contrast with the body font.

### Visual Motifs
- **Double-ruled border** under the masthead (CSS `border-bottom: 3px double`) — a classic broadsheet separator
- **Section labels** in all-caps, wide-tracked brick red with a trailing rule (`::after` pseudo-element)
- **Image placeholders** rendered as hatched diagonal stripes — editorial placeholders that read as intentional, not absent
- **Journals ticker** in dark umber — echoes the ink-heavy footer strips of 19th-century newspapers
- No rounded corners, no drop shadows, no gradients — all structure comes from rules and whitespace

---

## Layout

### Page Structure (top to bottom)

1. **Top Utility Bar** — blue, small; navigation links left, search + subscribe right
2. **Masthead** — three-column grid: date/provenance left · logo center · utility links right
3. **Primary Navigation** — centered, pipe-separated category links, horizontally scrollable on mobile
4. **Hero + Sidebar** — two-column: large featured story left, 4-item sidebar right
5. **Journals Ticker** — full-width umber band listing source journals
6. **Story Grid** — four equal columns, image + kicker + headline + dek + byline
7. **Wide + Narrow Row** — 2/3 wide feature left, 1/3 narrow story stack right
8. **Footer** — blue band: logo · tagline · links

### Grid Logic
- Max content width is unconstrained (full viewport); padding is `40px` on desktop, `16–20px` on mobile
- Column dividers use `border-right: 1px solid var(--cream-dark)` — never box shadows or backgrounds
- Section separation uses `border-bottom: 2px solid var(--umber)` for major breaks, `1px solid var(--cream-dark)` for minor

---

## Responsive Behavior

### Breakpoints

| Breakpoint | Behavior |
|---|---|
| > 900px | Full desktop layout |
| ≤ 900px | Tablet: masthead collapses to center-only; sidebar goes 2-column grid; story grid goes 2-column; top utility bar links hidden |
| ≤ 540px | Mobile: single column throughout; masthead simplified; nav scrolls horizontally; top utility bar hidden entirely |

### Mobile-specific decisions
- The **nav** becomes a horizontally scrolling strip with `overflow-x: auto` and hidden scrollbar — preserving all categories without a hamburger menu
- The **sidebar** collapses to a 2-column grid at tablet, then single column at mobile — each item separated by a bottom border
- The **hero image** shrinks from 340px → 220px → 200px tall across breakpoints
- The **logo** uses `clamp(48px, 7vw, 80px)` to scale fluidly without hard breakpoints
- The **footer** stacks vertically on mobile

---

## UX Behaviors

### Implemented
- **Hover states** on all headlines: `color` transitions to Prussian Blue (`#2c3e6b`)
- **Source links** styled distinctly (`↗` prefix, blue color) — reinforcing the aggregator model; every link leads out to an original journal
- **Top bar subscribe CTA** uses ochre background to draw attention without aggression
- **Nav active state** highlights the current section in brick red
- **Smooth font rendering** via `-webkit-font-smoothing: antialiased`
- **`text-wrap: pretty`** on headlines and deks — prevents orphaned single words

### Intentionally absent
- No JavaScript — the front page is pure HTML/CSS for speed and resilience
- No infinite scroll or pagination — the page presents a finite, curated edition (like a physical newspaper)
- No ads or sponsored content zones — the layout leaves no slots for them by design

---

## Content Model

Each story card carries:
- **Kicker** — content type (Essay, Fiction, Poetry, Interview, Art, Translation, Review)
- **Headline** — set in Cormorant Garamond
- **Dek** — short italic description in IM Fell English
- **Byline** — "by [Author]"
- **Source** — journal name, linked outward with `↗` indicator

The hero additionally shows a **large image zone** and a more generous dek. The sidebar omits images to prioritize density.

---

## Files

| File | Purpose |
|---|---|
| `Kopani Broadsheet.html` | Main responsive front page |
| `Kopani Broadsheet (bundle).html` | Self-contained offline bundle |
| `Kopani.html` | Design canvas with 3 layout explorations |

---

*Design by Kopani · Built in HTML/CSS · April 2026*
