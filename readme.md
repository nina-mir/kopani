# Kopani

Kopani is a discovery platform and editorial front page for independent literary journals. It curates standout poems, stories, and essays from small and mid-size magazines and sends readers back to the original publications to read the full work.

## What this repo contains

- Product and MVP planning documents (roadmaps, schemas, notes)
- Application code for the Kopani front end and data layer
- Scraper / ingestion framework (no scraped datasets)
- Configuration and infrastructure docs

> Note: Scraped data and any private content are stored separately in private infrastructure and are **not** included in this repository.

## High-level goals

- Make it easy for readers to discover great work from independent journals.
- Drive meaningful outbound traffic back to the journals that publish the work.
- Provide a maintainable ingestion and curation workflow for a small team or solo founder.

## MVP shape

The initial MVP focuses on:

- A curated, magazine-style homepage (“Kopani Post”)
- Journal profile pages
- Internal piece pages with short original blurbs and outbound links
- A simple taxonomy (journal, type, themes)
- Newsletter signup and basic analytics

## Running locally

> These steps are placeholders — adapt them to your actual stack.

```bash
# clone the repo
git clone https://github.com/<your-username>/kopani.git
cd kopani

# install dependencies
npm install

# start dev server
npm run dev
```

Create a `.env.local` (or equivalent) file based on `.env.example` for any required environment variables.

## Contributing

This project is in an early experimental phase. Bug reports, suggestions, and lightweight contributions are welcome via issues and pull requests.

Before contributing:

- Avoid committing any secrets or private data.
- Keep scraped data and proprietary content out of the public repo.
- Prefer small, focused PRs.

## License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.
