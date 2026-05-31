// src/scripts/searchPage.ts

import {
  getSearchResults,
  normalizeSearchText,
  type SearchIndexItem,
  type SearchSort,
} from "../lib/searchShared";

const INDEX_URL = "/search-index.json";

const form = document.querySelector<HTMLFormElement>("#kopani-search-form");
const input = document.querySelector<HTMLInputElement>("#kopani-search-input");
const sortSelect = document.querySelector<HTMLSelectElement>("#kopani-search-sort");
const statusEl = document.querySelector<HTMLElement>("#kopani-search-status");
const resultsEl = document.querySelector<HTMLElement>("#kopani-search-results");

let searchIndex: SearchIndexItem[] = [];
let hasLoadedIndex = false;

function isSearchSort(value: string | null): value is SearchSort {
  return (
    value === "relevance" ||
    value === "title-az" ||
    value === "shortest" ||
    value === "longest"
  );
}

function getInitialState(): { query: string; sort: SearchSort } {
  const params = new URLSearchParams(window.location.search);
  const query = params.get("q") ?? "";
  const sortParam = params.get("sort");

  return {
    query,
    sort: isSearchSort(sortParam) ? sortParam : "relevance",
  };
}

function setControls(query: string, sort: SearchSort): void {
  if (input) input.value = query;
  if (sortSelect) sortSelect.value = sort;
}

function updateUrl(query: string, sort: SearchSort): void {
  const params = new URLSearchParams();

  if (query.trim()) {
    params.set("q", query.trim());
  }

  if (sort !== "relevance") {
    params.set("sort", sort);
  }

  const nextUrl = params.toString()
    ? `${window.location.pathname}?${params.toString()}`
    : window.location.pathname;

  window.history.replaceState({}, "", nextUrl);
}

function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function formatContributors(
  label: string,
  contributors: SearchIndexItem["authors"],
): string {
  if (!contributors.length) return "";

  const names = contributors.map((person) => person.name).join(", ");

  return `${label}: ${names}`;
}

function formatReadingTime(item: SearchIndexItem): string {
  if (item.readTimeMinutes) {
    return `${item.readTimeMinutes} min`;
  }

  if (item.readingSortMinutes) {
    return `~${item.readingSortMinutes} min`;
  }

  return "";
}

function renderEmptyState(message: string): void {
  if (!resultsEl) return;

  resultsEl.innerHTML = `
    <div class="border border-ink/10 bg-linen/70 p-6">
      <p class="font-arno text-xl italic text-ochre">
        ${escapeHtml(message)}
      </p>
    </div>
  `;
}

function renderResults(items: SearchIndexItem[], query: string): void {
  if (!resultsEl || !statusEl) return;

  const trimmedQuery = query.trim();

  if (!hasLoadedIndex) {
    statusEl.textContent = "Loading search index…";
    resultsEl.innerHTML = "";
    return;
  }

  if (!trimmedQuery) {
    statusEl.textContent = `${searchIndex.length.toLocaleString()} pieces indexed.`;
    renderEmptyState("Enter a search term to begin.");
    return;
  }

  statusEl.textContent =
    items.length === 1
      ? `1 result for “${trimmedQuery}”.`
      : `${items.length.toLocaleString()} results for “${trimmedQuery}”.`;

  if (items.length === 0) {
    renderEmptyState("No matches found. Try a title, author, journal, or genre.");
    return;
  }

  resultsEl.innerHTML = items
    .map((item) => {
      const resultUrl = item.originalUrl || item.href;
      const byline = item.byline ? `By ${item.byline}` : "";
      const translators = formatContributors("Translated by", item.translators);
      const visualArtists = formatContributors("Visual art by", item.visualArtists);
      const readingTime = formatReadingTime(item);

      const metaParts = [
        item.contentTypeLabel,
        item.journalName,
        item.dateLabel,
        item.issueLabel,
        readingTime,
      ].filter(Boolean);

      const contributorParts = [
        byline,
        translators,
        visualArtists,
      ].filter(Boolean);

      const keywords = item.aiKeywords.slice(0, 6);

      return `
        <article class="border border-ink/10 bg-linen p-5 shadow-[0_1px_0_rgba(28,18,8,0.06)] transition hover:border-ink/25 md:p-6">
          <div class="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
            <div class="min-w-0">
              <p class="font-body text-xs uppercase tracking-[0.2em] text-brick">
                ${escapeHtml(metaParts.join(" · "))}
              </p>

              <h2 class="mt-3 font-display text-3xl leading-tight text-ink md:text-4xl">
                <a
                  href="${escapeHtml(resultUrl)}"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="hover:text-prussian"
                >
                  ${escapeHtml(item.title)}
                </a>
              </h2>

              ${
                item.subtitle
                  ? `<p class="mt-2 font-arno text-xl italic leading-snug text-ochre">${escapeHtml(item.subtitle)}</p>`
                  : ""
              }

              ${
                contributorParts.length
                  ? `<p class="mt-3 font-body text-sm leading-relaxed text-umber">${escapeHtml(contributorParts.join(" · "))}</p>`
                  : ""
              }

              ${
                item.dek
                  ? `<p class="mt-4 max-w-3xl font-arno text-lg leading-relaxed text-ink/80">${escapeHtml(item.dek)}</p>`
                  : ""
              }

              ${
                keywords.length
                  ? `<div class="mt-4 flex flex-wrap gap-2">
                      ${keywords
                        .map(
                          (keyword) =>
                            `<span class="border border-cream-dark px-2 py-1 font-mono text-[0.68rem] uppercase tracking-[0.12em] text-umber">${escapeHtml(keyword)}</span>`,
                        )
                        .join("")}
                    </div>`
                  : ""
              }
            </div>

            <a
              href="${escapeHtml(resultUrl)}"
              target="_blank"
              rel="noopener noreferrer"
              class="shrink-0 border border-ink/30 px-3 py-2 text-center font-body text-xs uppercase tracking-[0.18em] text-ink hover:border-prussian hover:text-prussian"
            >
              Read at journal
            </a>
          </div>
        </article>
      `;
    })
    .join("");
}

function runSearch(): void {
  if (!input || !sortSelect) return;

  const query = input.value;
  const sortValue = isSearchSort(sortSelect.value)
    ? sortSelect.value
    : "relevance";

  updateUrl(query, sortValue);

  const normalizedQuery = normalizeSearchText(query);
  const results = getSearchResults(searchIndex, normalizedQuery, sortValue);

  renderResults(results, query);
}

async function loadSearchIndex(): Promise<void> {
  if (!statusEl || !resultsEl) return;

  try {
    const response = await fetch(INDEX_URL);

    if (!response.ok) {
      throw new Error(`Search index request failed: ${response.status}`);
    }

    searchIndex = (await response.json()) as SearchIndexItem[];
    hasLoadedIndex = true;

    const initialState = getInitialState();
    setControls(initialState.query, initialState.sort);

    runSearch();
  } catch (error) {
    console.error(error);

    statusEl.textContent = "Search is unavailable right now.";
    resultsEl.innerHTML = `
      <div class="border border-brick/30 bg-linen p-6">
        <p class="font-arno text-xl italic text-brick">
          Could not load the search index.
        </p>
        <p class="mt-2 font-body text-sm text-umber">
          Check that /search-index.json is being generated and that the SQLite database is available during build/dev.
        </p>
      </div>
    `;
  }
}

form?.addEventListener("submit", (event) => {
  event.preventDefault();
  runSearch();
});

input?.addEventListener("input", () => {
  runSearch();
});

sortSelect?.addEventListener("change", () => {
  runSearch();
});

loadSearchIndex();