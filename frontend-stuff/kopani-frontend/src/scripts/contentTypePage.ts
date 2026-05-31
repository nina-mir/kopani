// src/scripts/contentTypePage.ts

/**
 * Local filter/sort behavior for content-type pages.
 *
 * Used on pages like:
 * - /poetry
 * - /essays
 * - /fiction
 *
 * This does NOT fetch /search-index.json.
 * It only works with cards already rendered on the current page.
 */

type ContentSort = "default" | "title-az" | "shortest" | "longest";

const filterInput = document.querySelector<HTMLInputElement>(
  "[data-content-filter-input]",
);

const sortSelect = document.querySelector<HTMLSelectElement>(
  "[data-content-sort-select]",
);

const statusEl = document.querySelector<HTMLElement>(
  "[data-content-results-status]",
);

const gridEl = document.querySelector<HTMLElement>("[data-content-grid]");

const emptyEl = document.querySelector<HTMLElement>("[data-content-empty]");

const cards = Array.from(
  document.querySelectorAll<HTMLElement>("[data-content-card]"),
);

function normalizeText(value: string): string {
  return value
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[’‘]/g, "'")
    .replace(/[“”]/g, '"')
    .replace(/[_-]+/g, " ")
    .replace(/[^\p{Letter}\p{Number}'" ]+/gu, " ")
    .replace(/\s+/g, " ")
    .trim()
    .toLowerCase();
}

function getSortValue(): ContentSort {
  const value = sortSelect?.value;

  if (
    value === "default" ||
    value === "title-az" ||
    value === "shortest" ||
    value === "longest"
  ) {
    return value;
  }

  return "default";
}

function getOriginalIndex(card: HTMLElement): number {
  const raw = card.dataset.originalIndex;
  const value = Number(raw);

  return Number.isFinite(value) ? value : 0;
}

function getTitle(card: HTMLElement): string {
  return normalizeText(card.dataset.title ?? "");
}

function getReadingSort(card: HTMLElement): number | null {
  const raw = card.dataset.readingSort;

  if (!raw) return null;

  const value = Number(raw);

  if (!Number.isFinite(value)) return null;
  if (value <= 0) return null;

  return value;
}

function compareCards(a: HTMLElement, b: HTMLElement, sort: ContentSort): number {
  if (sort === "default") {
    return getOriginalIndex(a) - getOriginalIndex(b);
  }

  if (sort === "title-az") {
    const titleCompare = getTitle(a).localeCompare(getTitle(b));

    if (titleCompare !== 0) return titleCompare;

    return getOriginalIndex(a) - getOriginalIndex(b);
  }

  const aReading = getReadingSort(a);
  const bReading = getReadingSort(b);

  /**
   * Unknown reading times should always go to the bottom,
   * whether sorting shortest-first or longest-first.
   */
  if (aReading === null && bReading === null) {
    return getOriginalIndex(a) - getOriginalIndex(b);
  }

  if (aReading === null) return 1;
  if (bReading === null) return -1;

  if (sort === "shortest") {
    return aReading - bReading || getOriginalIndex(a) - getOriginalIndex(b);
  }

  if (sort === "longest") {
    return bReading - aReading || getOriginalIndex(a) - getOriginalIndex(b);
  }

  return getOriginalIndex(a) - getOriginalIndex(b);
}

function updateStatus(visibleCount: number, totalCount: number): void {
  if (!statusEl) return;

  if (totalCount === 0) {
    statusEl.textContent = "No pieces";
    return;
  }

  if (visibleCount === totalCount) {
    statusEl.textContent = `Showing all ${totalCount}`;
    return;
  }

  statusEl.textContent = `Showing ${visibleCount} of ${totalCount}`;
}

function applyFilterAndSort(): void {
  if (!gridEl) return;

  const query = normalizeText(filterInput?.value ?? "");
  const sort = getSortValue();

  let visibleCount = 0;

  for (const card of cards) {
    const searchText = card.dataset.searchText ?? "";
    const isMatch = !query || searchText.includes(query);

    card.hidden = !isMatch;

    if (isMatch) {
      visibleCount += 1;
    }
  }

  const sortedCards = [...cards].sort((a, b) => compareCards(a, b, sort));

  for (const card of sortedCards) {
    gridEl.appendChild(card);
  }

  updateStatus(visibleCount, cards.length);

  if (emptyEl) {
    emptyEl.hidden = visibleCount !== 0;
  }
}

filterInput?.addEventListener("input", applyFilterAndSort);
sortSelect?.addEventListener("change", applyFilterAndSort);

applyFilterAndSort();