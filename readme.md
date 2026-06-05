![Kopani — the independent literary press, gathered.](frontend-stuff\kopani-frontend\public\og\kopani-og-wordmark.jpg)

# Kopani

Kopani is discovery and compensation infrastructure for the independent literary press.

It begins as a rights-respecting literary index that helps readers discover essays, fiction, poetry, interviews, translations, and visual art from independent journals without republishing copyrighted material. Kopani sends readers back to the original journals and is designed to make literary work more discoverable, more legible, and eventually more supportable over time.

## Why Kopani

Independent journals publish extraordinary work, but much of it becomes hard to find after publication. Readers have to search journal by journal, faculty have limited ways to build contemporary reading lists, and writers, translators, and artists rarely share in the long-term value their work creates.

Kopani is built to address that fragmentation by gathering structured metadata across journals into one searchable system.

## What the product does

- Browses real pieces from independent literary journals on the homepage
- Supports search across titles, journals, authors, translators, visual artists, genres, descriptions, keywords, and reading time
- Surfaces publication and contributor metadata in a consistent, searchable format
- Links readers back to original sources instead of republishing copyrighted work

## Campus use case

The first business wedge is campuses.

Kopani can function as a contemporary reading center and a hidden literary alumni graph. The campus layer surfaces contributor-campus relationships from bios, connecting writers, translators, artists, institutions, journals, and pieces that are otherwise scattered across the web.

## Long-term vision

Kopani starts with discovery, compounds into a literary reputation graph, and aims to become financial infrastructure for independent publishing.

The longer-term model is piece-level support: readers, alumni, donors, and institutions should be able to direct support to specific works, with verified routing to writers, translators, visual artists, or rights-approved journal recipients. The prototype explores a future 90/10 model where most support flows to the people and publications that made the work possible.

## Copyright

Kopani does **not** republish copyrighted material.

It indexes metadata, search fields, and descriptive information, then directs readers to the original journal pages where the work appears.

## Repository structure

- `frontend-stuff/kopani-frontend/` — frontend application
- Scraping, ingestion, and metadata workflows — source collection and normalization pipeline
- Project data/modeling code — structured records, search fields, and schema work

## Status

This repository is an MVP in active development, focused on ingestion across journals, metadata modeling, discovery UX, and product validation.


## License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.
