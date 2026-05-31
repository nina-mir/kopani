// src/pages/search-index.json.ts
import type { APIRoute } from "astro";
import { getSearchIndexItems } from "../lib/db";

/**
 * Build-time JSON endpoint for global Kopani search.
 *
 * Source file:
 *   src/pages/search-index.json.ts
 *
 * Public URL:
 *   /search-index.json
 *
 * Astro removes the final .ts extension, so this file becomes a real
 * static JSON file during `astro build`.
 */
export const prerender = true;

export const GET: APIRoute = () => {
  const items = getSearchIndexItems();

  return new Response(JSON.stringify(items), {
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "public, max-age=0, must-revalidate",
    },
  });
};