# Building a Literary Magazine with Astro + Tailwind CSS

A comprehensive reference for building a responsive, performant editorial site — poetry, fiction, interviews — styled with Tailwind CSS v4, powered by Astro's content layer, and optionally enhanced with Radix UI primitives.

---

## 1. Project Setup

### Create the Astro Project

```bash
npm create astro@latest literary-mag
cd literary-mag
```

Choose the "Empty" template. Select TypeScript (recommended).

### Install Tailwind CSS v4

The old `@astrojs/tailwind` integration is **deprecated** for Tailwind v4. Use the official Vite plugin instead:

```bash
npx astro add tailwind
```

This does three things automatically: installs `tailwindcss` and `@tailwindcss/vite`, wires the plugin into your Astro config, and creates a starter CSS file.

If you prefer manual setup:

```bash
npm install tailwindcss @tailwindcss/vite
```

Then update `astro.config.mjs`:

```js
// astro.config.mjs
import { defineConfig } from "astro/config";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  vite: {
    plugins: [tailwindcss()],
  },
});
```

Create your global stylesheet at `src/styles/global.css`:

```css
@import "tailwindcss";
```

That single line is all Tailwind v4 needs. No `tailwind.config.js` required — configuration now lives in CSS.

### Install the Typography Plugin

Essential for rendering long-form prose (your poems, fiction, interviews):

```bash
npm install @tailwindcss/typography
```

Add it to your CSS file:

```css
/* src/styles/global.css */
@import "tailwindcss";
@plugin "@tailwindcss/typography";
```

---

## 2. Project Structure

```
literary-mag/
├── public/
│   ├── fonts/                  # Self-hosted font files (woff2)
│   ├── images/
│   │   ├── authors/            # Author headshots
│   │   ├── covers/             # Issue cover art
│   │   └── editorial/          # Article hero images
│   ├── icons/                  # SVG favicons, touch icons
│   └── favicon.svg
├── src/
│   ├── components/
│   │   ├── ui/                 # Reusable primitives (Card, Badge, Tag)
│   │   ├── layout/             # Header, Footer, Nav, Sidebar
│   │   └── blocks/             # Composed sections (HeroFeature, ArticleGrid)
│   ├── content/
│   │   └── config.ts           # Content collection schemas (Zod)
│   ├── data/
│   │   ├── articles.json       # Article metadata if using JSON source
│   │   └── authors.json        # Author bios
│   ├── layouts/
│   │   ├── BaseLayout.astro    # HTML shell, imports global.css
│   │   ├── ArticleLayout.astro # Single-piece reading view
│   │   └── SectionLayout.astro # Category landing (Poetry, Fiction, etc.)
│   ├── pages/
│   │   ├── index.astro         # Homepage / NPR-style front page
│   │   ├── poetry/
│   │   │   ├── index.astro     # Poetry section landing
│   │   │   └── [slug].astro    # Individual poem page
│   │   ├── fiction/
│   │   ├── interviews/
│   │   └── about.astro
│   ├── styles/
│   │   └── global.css          # Tailwind import + @theme + @apply layers
│   └── lib/
│       └── db.ts               # SQLite helper (if using database)
├── astro.config.mjs
├── package.json
└── tsconfig.json
```

### Key Structural Decisions

**`components/ui/`** — Atomic, style-only components. A `Card.astro` here knows nothing about articles; it just renders a slot with a visual container.

**`components/blocks/`** — Composed components that combine UI primitives with data. `HeroFeature.astro` fetches the featured article and renders it inside a `Card`.

**`data/`** — JSON files or database connectors. Astro's content layer can ingest these at build time.

**`lib/`** — Utility functions, database clients, formatters. Keep data-fetching logic here, not in components.

### Images and Icons

Use Astro's built-in `<Image />` component from `astro:assets` for automatic optimization:

```astro
---
import { Image } from "astro:assets";
import heroImg from "../images/editorial/summer-issue.jpg";
---
<Image src={heroImg} alt="Summer issue cover" width={1200} />
```

For icons, use inline SVGs or a lightweight icon set. Avoid icon font libraries — they ship unused glyphs. Good options: copy individual SVGs from [Lucide](https://lucide.dev) or [Phosphor](https://phosphoricons.com) into a `src/components/icons/` folder.

---

## 3. Adobe Fonts Integration

Add your Adobe Fonts embed code in the `<head>` of `BaseLayout.astro`:

```astro
---
// src/layouts/BaseLayout.astro
import "../styles/global.css";

const { title = "The Literary Review" } = Astro.props;
---
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{title}</title>
    <link rel="stylesheet" href="https://use.typekit.net/YOUR_KIT_ID.css" />
  </head>
  <body class="min-h-screen bg-stone-50 text-stone-900 antialiased">
    <slot />
  </body>
</html>
```

Then register your fonts as design tokens in your CSS:

```css
/* src/styles/global.css */
@import "tailwindcss";
@plugin "@tailwindcss/typography";

@theme {
  --font-display: "freight-display-pro", "Georgia", serif;
  --font-body: "acumin-pro", "Helvetica Neue", sans-serif;
  --font-mono: "source-code-pro", monospace;
}
```

Now you can use them anywhere: `font-display`, `font-body`, `font-mono`.

---

## 4. Configuring Design Tokens with `@theme`

In Tailwind v4, all customization lives in CSS via the `@theme` directive. No JavaScript config file needed:

```css
@theme {
  /* Typography */
  --font-display: "freight-display-pro", "Georgia", serif;
  --font-body: "acumin-pro", "Helvetica Neue", sans-serif;

  /* Colors — editorial palette */
  --color-ink: #1a1a1a;
  --color-paper: #faf9f6;
  --color-accent: #c0392b;
  --color-muted: #6b7280;
  --color-divider: #e5e1db;

  /* Spacing scale extensions */
  --spacing-18: 4.5rem;
  --spacing-88: 22rem;

  /* Custom breakpoint */
  --breakpoint-3xl: 120rem;
}
```

These become usable as utilities immediately: `text-ink`, `bg-paper`, `border-divider`, `text-accent`.

---

## 5. Using `@apply` in Tailwind v4

`@apply` still works in v4 and remains useful for creating reusable component classes — especially for prose-heavy editorial sites where you want consistent typographic styles.

### How It Works

```css
/* src/styles/global.css */

@utility article-title {
  @apply font-display text-3xl leading-tight tracking-tight text-ink
    md:text-4xl lg:text-5xl;
}

@utility article-byline {
  @apply font-body text-sm uppercase tracking-widest text-muted;
}

@utility section-label {
  @apply font-body text-xs font-bold uppercase tracking-[0.2em] text-accent;
}

@utility prose-body {
  @apply font-body text-lg leading-relaxed text-ink/90;
}

@utility card-surface {
  @apply rounded-sm border border-divider bg-white
    shadow-xs transition-shadow hover:shadow-md;
}
```

### Key v4 Changes to Know

In Tailwind v4, custom utilities are registered with `@utility` instead of putting them inside `@layer components`. The `@layer components` approach from v3 still works for backwards compatibility, but `@utility` is the idiomatic v4 way — it makes your custom classes work with variants like `hover:`, `md:`, etc.

If you use `@apply` inside a scoped `<style>` block in a `.astro` file (or Vue/Svelte SFC), you need the `@reference` directive so the compiler knows your theme:

```astro
<style>
  @reference "../../styles/global.css";

  .hero-title {
    @apply font-display text-5xl text-ink;
  }
</style>
```

### When NOT to Use `@apply`

Avoid `@apply` for one-off styles — just use utility classes directly in your markup. Reserve it for patterns you repeat 5+ times across the codebase. Overusing `@apply` defeats the purpose of utility-first CSS and makes your stylesheets harder to maintain.

---

## 6. Data Sources — JSON and SQLite

### Option A: JSON via Astro Content Collections

Define a content collection with the `file()` loader for a single JSON file:

```ts
// src/content.config.ts
import { defineCollection, z } from "astro:content";
import { file } from "astro/loaders";

const articles = defineCollection({
  loader: file("src/data/articles.json"),
  schema: z.object({
    id: z.string(),
    title: z.string(),
    author: z.string(),
    category: z.enum(["poetry", "fiction", "interview"]),
    excerpt: z.string(),
    heroImage: z.string().optional(),
    publishDate: z.coerce.date(),
    featured: z.boolean().default(false),
    tags: z.array(z.string()).default([]),
  }),
});

const authors = defineCollection({
  loader: file("src/data/authors.json"),
  schema: z.object({
    id: z.string(),
    name: z.string(),
    bio: z.string(),
    headshot: z.string().optional(),
  }),
});

export const collections = { articles, authors };
```

Sample `articles.json`:

```json
[
  {
    "id": "the-weight-of-rain",
    "title": "The Weight of Rain",
    "author": "author-maria-elena",
    "category": "poetry",
    "excerpt": "A meditation on memory and the persistence of weather.",
    "heroImage": "/images/editorial/rain.jpg",
    "publishDate": "2026-04-15",
    "featured": true,
    "tags": ["nature", "memory", "spring"]
  }
]
```

Query it in any `.astro` page:

```astro
---
import { getCollection } from "astro:content";

const allArticles = await getCollection("articles");
const featured = allArticles.filter((a) => a.data.featured);
const poetry = allArticles.filter((a) => a.data.category === "poetry");
---
```

### Option B: SQLite via better-sqlite3

For a larger editorial database with complex queries:

```bash
npm install better-sqlite3
npm install -D @types/better-sqlite3
```

Create a database helper:

```ts
// src/lib/db.ts
import Database from "better-sqlite3";
import path from "node:path";

const db = new Database(path.resolve("src/data/magazine.db"), {
  readonly: true,
});

export interface Article {
  id: string;
  title: string;
  author_name: string;
  category: "poetry" | "fiction" | "interview";
  excerpt: string;
  hero_image: string | null;
  publish_date: string;
  featured: number;
}

export function getFeaturedArticles(limit = 5): Article[] {
  return db
    .prepare(
      `SELECT a.*, au.name as author_name
       FROM articles a
       JOIN authors au ON a.author_id = au.id
       WHERE a.featured = 1
       ORDER BY a.publish_date DESC
       LIMIT ?`
    )
    .all(limit) as Article[];
}

export function getArticlesByCategory(category: string): Article[] {
  return db
    .prepare(
      `SELECT a.*, au.name as author_name
       FROM articles a
       JOIN authors au ON a.author_id = au.id
       WHERE a.category = ?
       ORDER BY a.publish_date DESC`
    )
    .all(category) as Article[];
}

export function getArticleBySlug(slug: string): Article | undefined {
  return db
    .prepare(
      `SELECT a.*, au.name as author_name
       FROM articles a
       JOIN authors au ON a.author_id = au.id
       WHERE a.id = ?`
    )
    .get(slug) as Article | undefined;
}
```

Use it in a page:

```astro
---
// src/pages/index.astro
import BaseLayout from "../layouts/BaseLayout.astro";
import { getFeaturedArticles } from "../lib/db";

const featured = getFeaturedArticles(5);
---
<BaseLayout title="Home">
  {featured.map((article) => (
    <article>
      <h2>{article.title}</h2>
      <p>{article.excerpt}</p>
    </article>
  ))}
</BaseLayout>
```

**Which to choose?** JSON via content collections is simpler, has built-in type safety, and works beautifully for editorial sites with fewer than ~1,000 pieces. SQLite shines when you have complex relational queries, full-text search needs, or thousands of entries.

---

## 7. Building Custom Components

### ArticleCard Component

```astro
---
// src/components/ui/ArticleCard.astro

export interface Props {
  title: string;
  author: string;
  category: string;
  excerpt: string;
  heroImage?: string;
  slug: string;
  featured?: boolean;
}

const { title, author, category, excerpt, heroImage, slug, featured } = Astro.props;
---

<article
  class:list={[
    "group flex flex-col overflow-hidden border-b border-divider pb-6",
    featured && "col-span-full md:flex-row md:gap-8",
  ]}
>
  {heroImage && (
    <a
      href={`/${category}/${slug}`}
      class:list={[
        "block overflow-hidden",
        featured
          ? "md:w-1/2 lg:w-3/5"
          : "aspect-[16/10]",
      ]}
    >
      <img
        src={heroImage}
        alt=""
        class="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
        loading="lazy"
        decoding="async"
      />
    </a>
  )}

  <div class:list={["flex flex-col justify-center", featured && "md:w-1/2 lg:w-2/5"]}>
    <span class="section-label mb-2">{category}</span>

    <a href={`/${category}/${slug}`}>
      <h2
        class:list={[
          "font-display leading-tight tracking-tight text-ink",
          "transition-colors group-hover:text-accent",
          featured ? "text-3xl md:text-4xl" : "text-xl md:text-2xl",
        ]}
      >
        {title}
      </h2>
    </a>

    <p class="mt-3 font-body text-base leading-relaxed text-muted line-clamp-3">
      {excerpt}
    </p>

    <span class="article-byline mt-4">By {author}</span>
  </div>
</article>
```

### SectionHeader Component

```astro
---
// src/components/ui/SectionHeader.astro

export interface Props {
  label: string;
  href?: string;
}

const { label, href } = Astro.props;
---

<div class="flex items-center justify-between border-b-2 border-ink pb-2 mb-6">
  <h2 class="font-display text-lg font-bold uppercase tracking-wide text-ink">
    {label}
  </h2>
  {href && (
    <a
      href={href}
      class="font-body text-xs font-semibold uppercase tracking-widest text-accent
             hover:underline hover:underline-offset-4"
    >
      See All →
    </a>
  )}
</div>
```

### Homepage Grid (NPR-Style Layout)

```astro
---
// src/pages/index.astro
import BaseLayout from "../layouts/BaseLayout.astro";
import ArticleCard from "../components/ui/ArticleCard.astro";
import SectionHeader from "../components/ui/SectionHeader.astro";
import { getCollection } from "astro:content";

const articles = await getCollection("articles");
const featured = articles.find((a) => a.data.featured);
const poetry = articles
  .filter((a) => a.data.category === "poetry" && !a.data.featured)
  .slice(0, 4);
const fiction = articles
  .filter((a) => a.data.category === "fiction")
  .slice(0, 4);
const interviews = articles
  .filter((a) => a.data.category === "interview")
  .slice(0, 3);
---

<BaseLayout title="The Literary Review">
  <main class="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">

    <!-- HERO: Featured piece, full width -->
    {featured && (
      <section class="mb-12">
        <ArticleCard
          title={featured.data.title}
          author={featured.data.author}
          category={featured.data.category}
          excerpt={featured.data.excerpt}
          heroImage={featured.data.heroImage}
          slug={featured.id}
          featured
        />
      </section>
    )}

    <!-- NPR-STYLE 3-COLUMN GRID -->
    <div class="grid grid-cols-1 gap-10 md:grid-cols-2 lg:grid-cols-3">

      <!-- Column 1: Poetry -->
      <section>
        <SectionHeader label="Poetry" href="/poetry" />
        <div class="flex flex-col gap-8">
          {poetry.map((p) => (
            <ArticleCard
              title={p.data.title}
              author={p.data.author}
              category={p.data.category}
              excerpt={p.data.excerpt}
              heroImage={p.data.heroImage}
              slug={p.id}
            />
          ))}
        </div>
      </section>

      <!-- Column 2: Fiction -->
      <section>
        <SectionHeader label="Fiction" href="/fiction" />
        <div class="flex flex-col gap-8">
          {fiction.map((f) => (
            <ArticleCard
              title={f.data.title}
              author={f.data.author}
              category={f.data.category}
              excerpt={f.data.excerpt}
              heroImage={f.data.heroImage}
              slug={f.id}
            />
          ))}
        </div>
      </section>

      <!-- Column 3: Interviews -->
      <section>
        <SectionHeader label="Interviews" href="/interviews" />
        <div class="flex flex-col gap-8">
          {interviews.map((i) => (
            <ArticleCard
              title={i.data.title}
              author={i.data.author}
              category={i.data.category}
              excerpt={i.data.excerpt}
              heroImage={i.data.heroImage}
              slug={i.id}
            />
          ))}
        </div>
      </section>
    </div>
  </main>
</BaseLayout>
```

---

## 8. Responsive Design — Seamless Across All Devices

### Tailwind v4 Breakpoints

Default breakpoints and what they roughly correspond to:

| Prefix | Min-Width | Devices                              |
|--------|-----------|--------------------------------------|
| `sm`   | 640px     | Large phones (landscape)             |
| `md`   | 768px     | Tablets (iPad Mini, Galaxy Tab)      |
| `lg`   | 1024px    | iPad Air/Pro, small laptops          |
| `xl`   | 1280px    | Laptops, desktops                    |
| `2xl`  | 1536px    | Large monitors                       |

Add a custom breakpoint for ultra-wide in your `@theme`:

```css
@theme {
  --breakpoint-3xl: 120rem;  /* 1920px */
}
```

### Mobile-First Grid Strategy

The NPR layout translates to this responsive cascade:

```
Phone (< 640px):       1 column, stacked vertically
Tablet (md: 768px):    2 columns
Desktop (lg: 1024px):  3 columns + sidebar
Wide (xl: 1280px):     3 columns, wider gutters
```

```html
<div class="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3 xl:gap-10">
  <!-- content -->
</div>
```

### Targeting Specific Devices

For Samsung Galaxy Fold and other foldable screens, the key issue is the narrow outer screen (~280px). Handle it:

```css
/* Extremely narrow screens — Galaxy Fold outer display */
@custom-variant fold (width < 360px);
```

Use it: `fold:text-sm fold:px-2`.

For iPad-specific landscape layouts, combine `md` with `orientation` if needed:

```css
@custom-variant tablet-landscape (768px <= width < 1024px) and (orientation: landscape);
```

### Essential Responsive Patterns

**Fluid typography** — Scale font sizes smoothly between breakpoints:

```css
@theme {
  --font-size-fluid-xl: clamp(1.5rem, 1rem + 2vw, 3rem);
}
```

**Container queries** — Let cards respond to their container, not the viewport. Tailwind v4 supports these natively:

```html
<div class="@container">
  <div class="flex flex-col @md:flex-row @md:gap-6">
    <!-- Card content adapts to its parent container width -->
  </div>
</div>
```

**Safe area insets** — Critical for phones with notches and dynamic islands:

```css
body {
  padding-left: env(safe-area-inset-left);
  padding-right: env(safe-area-inset-right);
  padding-bottom: env(safe-area-inset-bottom);
}
```

**Touch targets** — All tappable elements should be at least 44×44px on mobile:

```html
<a href="/poetry" class="inline-flex items-center min-h-[44px] min-w-[44px] px-4 py-3">
  Poetry
</a>
```

**Image responsiveness** — Use `srcset` with Astro's image optimization:

```astro
---
import { Image } from "astro:assets";
import hero from "../images/editorial/hero.jpg";
---
<Image
  src={hero}
  widths={[400, 800, 1200, 1600]}
  sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
  alt="Feature story"
  class="w-full h-auto object-cover"
/>
```

---

## 9. Using Radix UI with Astro

Radix primitives are React-based, so they require Astro's React integration and ship JavaScript to the client. Use them sparingly — only for interactive components that need accessibility guarantees (modals, dropdowns, accordions, tooltips).

### Setup

```bash
npx astro add react
npm install @radix-ui/react-dialog @radix-ui/react-dropdown-menu @radix-ui/react-accordion
```

**Critical config** — Add this to `astro.config.mjs` to avoid SSR build errors:

```js
export default defineConfig({
  integrations: [react()],
  vite: {
    plugins: [tailwindcss()],
    ssr: {
      noExternal: [
        "@radix-ui/react-dialog",
        "@radix-ui/react-dropdown-menu",
        "@radix-ui/react-accordion",
      ],
    },
  },
});
```

### Example: Mobile Nav with Radix Dialog

```tsx
// src/components/ui/MobileNav.tsx
import * as Dialog from "@radix-ui/react-dialog";

const navLinks = [
  { label: "Poetry", href: "/poetry" },
  { label: "Fiction", href: "/fiction" },
  { label: "Interviews", href: "/interviews" },
  { label: "About", href: "/about" },
];

export default function MobileNav() {
  return (
    <Dialog.Root>
      <Dialog.Trigger asChild>
        <button
          className="inline-flex items-center justify-center rounded-sm p-2
                     text-ink hover:bg-stone-100 lg:hidden"
          aria-label="Open navigation"
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="3" y1="6" x2="21" y2="6" />
            <line x1="3" y1="12" x2="21" y2="12" />
            <line x1="3" y1="18" x2="21" y2="18" />
          </svg>
        </button>
      </Dialog.Trigger>

      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm
                                   data-[state=open]:animate-in data-[state=open]:fade-in" />
        <Dialog.Content className="fixed inset-y-0 left-0 z-50 w-72 bg-paper p-8 shadow-lg
                                    data-[state=open]:animate-in data-[state=open]:slide-in-from-left">
          <Dialog.Title className="font-display text-xl font-bold mb-8">
            The Literary Review
          </Dialog.Title>

          <nav className="flex flex-col gap-4">
            {navLinks.map((link) => (
              <a
                key={link.href}
                href={link.href}
                className="font-body text-lg text-ink hover:text-accent
                           transition-colors py-2 border-b border-divider"
              >
                {link.label}
              </a>
            ))}
          </nav>

          <Dialog.Close asChild>
            <button className="absolute top-4 right-4 p-2" aria-label="Close">
              ✕
            </button>
          </Dialog.Close>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
```

Use it in Astro with client directive — this is the island architecture at work:

```astro
---
import MobileNav from "../components/ui/MobileNav";
---
<header>
  <MobileNav client:load />
  <!-- Desktop nav renders as static HTML, no JS -->
  <nav class="hidden lg:flex gap-8">
    <a href="/poetry">Poetry</a>
    <a href="/fiction">Fiction</a>
  </nav>
</header>
```

### When to Use Radix vs. Pure Astro/CSS

| Component     | Use Radix?   | Why                                         |
|---------------|-------------|----------------------------------------------|
| Modal/Dialog  | Yes         | Focus trapping, escape handling, aria        |
| Dropdown menu | Yes         | Keyboard nav, positioning, screen readers    |
| Accordion/FAQ | Maybe       | CSS `<details>` may suffice                  |
| Tooltip       | Yes         | Positioning logic is complex                 |
| Navigation    | Probably no | A `<nav>` with links is semantic enough      |
| Cards         | No          | Pure HTML/CSS, no interactivity needed        |
| Tabs          | Maybe       | CSS-only tabs work for simple cases           |

Rule of thumb: if the component needs focus management, keyboard navigation, or complex ARIA patterns — use Radix. If it's purely visual, keep it as a static Astro component with zero JavaScript.

### Using shadcn/ui as an Alternative

If you want pre-styled Radix components with Tailwind, shadcn/ui works with Astro via the React integration. It's a copy-paste component library (not an npm package), so you own the code:

```bash
npx shadcn@latest init
npx shadcn@latest add dialog dropdown-menu
```

Components land in `src/components/ui/` and can be customized directly.

---

## 10. Performance Notes

### What Astro Gives You for Free

Astro ships **zero JavaScript by default**. Your article pages, category listings, and homepage are pure HTML + CSS. This is already faster than any SPA framework for a reading-heavy site.

### Additional Optimizations

**Image optimization** — Always use `astro:assets` for automatic WebP/AVIF conversion, responsive `srcset`, and lazy loading:

```astro
---
import { Image } from "astro:assets";
---
<Image src={myImage} alt="..." width={800} format="avif" />
```

**Font loading** — Adobe Fonts loads async by default, which is good. Add `font-display: swap` in your CSS as a fallback safety net:

```css
@font-face {
  font-family: "freight-display-pro";
  font-display: swap;
}
```

For even better performance, self-host your fonts (download WOFF2 files from Adobe Fonts if your license allows) and preload the critical ones:

```html
<link rel="preload" href="/fonts/freight-display-bold.woff2" as="font" type="font/woff2" crossorigin />
```

**CSS bundle** — Tailwind v4's engine is dramatically faster than v3. JIT compilation means only the classes you use end up in the output. A typical editorial site produces ~15-30KB of CSS.

**Minimize client directives** — Every `client:load` or `client:visible` directive ships JavaScript. Audit your components:

| Directive         | Use When                                      |
|-------------------|-----------------------------------------------|
| `client:load`     | Must be interactive immediately (mobile nav)  |
| `client:visible`  | Can wait until scrolled into view             |
| `client:idle`     | Can wait until browser is idle                |
| `client:media`    | Only needed at certain breakpoints            |
| (none)            | Static content — **default, prefer this**     |

**Prefetching** — Astro supports link prefetching out of the box. Enable it in your config:

```js
export default defineConfig({
  prefetch: {
    defaultStrategy: "hover",
  },
});
```

**Static output** — For a literary magazine with infrequent updates, use `output: "static"` (the default). Your entire site becomes a folder of HTML files — deploy to any CDN (Cloudflare Pages, Netlify, Vercel) for near-instant global delivery.

**View Transitions** — Astro has built-in support for smooth page transitions that make navigation feel app-like without a SPA:

```astro
---
// In BaseLayout.astro
import { ViewTransitions } from "astro:transitions";
---
<head>
  <ViewTransitions />
</head>
```

---

## 11. Dark Mode

Tailwind v4 supports `dark:` variants natively. Use the class strategy for manual toggle:

```css
/* In your global.css, after @import "tailwindcss" */
@custom-variant dark (&:where(.dark, .dark *));
```

Define dark palette values:

```css
:root {
  --color-ink: #1a1a1a;
  --color-paper: #faf9f6;
}

.dark {
  --color-ink: #e5e1db;
  --color-paper: #1a1a1a;
}
```

Then use `@theme inline` so Tailwind picks up the CSS variables:

```css
@theme inline {
  --color-ink: var(--color-ink);
  --color-paper: var(--color-paper);
}
```

Your existing `text-ink` and `bg-paper` classes now automatically respond to the `.dark` class on `<html>`.

---

## 12. Quick Reference

### Useful Commands

```bash
npm run dev          # Start dev server with HMR
npm run build        # Production build
npm run preview      # Preview the production build locally
npx astro add react  # Add React integration
npx astro add mdx    # Add MDX support (useful for interactive articles)
```

### Recommended VS Code Extensions

- **Astro** — Syntax highlighting, IntelliSense for `.astro` files
- **Tailwind CSS IntelliSense** — Autocomplete for utility classes
- **PostCSS Language Support** — Proper syntax highlighting for `@theme`, `@utility`

### Further Reading

- [Tailwind v4 docs](https://tailwindcss.com/docs)
- [Astro content collections](https://docs.astro.build/en/guides/content-collections/)
- [Astro image optimization](https://docs.astro.build/en/guides/images/)
- [Radix UI primitives](https://www.radix-ui.com/primitives)
- [shadcn/ui + Astro template](https://astro.build/themes/details/astro-tailwindcss-shadcnui-template/)
- [Tailwind typography plugin](https://tailwindcss.com/docs/typography-plugin)
