# Threepenny Review Progress

## Overview

Work on *Threepenny Review* is still at an early exploratory stage. The current focus is issue-level discovery, specifically building and testing a `discover_issue_urls` step before moving on to full piece scraping.

## What has been done

- Began defining the source in terms of the broader Kopani scraping pipeline.
- Treated this as a discovery-first workflow, where URLs and issue-related metadata are identified before deeper normalization.
- Kept the work aligned with the current MVP rule of storing issue information on pieces rather than creating a separate issues table.
- Kept the approach conservative around author data, favoring raw capture first and manual cleanup later if needed.

## Current approach

The Threepenny work fits the existing ingestion model: first discover candidate piece URLs, then scrape piece-level metadata, then review uncertain cases before normalization. This matches the broader project rule that messy source data should not be forced too early into fully normalized author records.

## What remains

- Continue testing `discover_issue_urls` across more issue pages.
- Document recurring edge cases and decide which should remain manual-review cases.
- Move from issue discovery to piece-page scraping only after discovery behavior is stable enough to trust.
- Add Threepenny-specific notes to the project files once the source structure is better understood.

## Status

Threepenny Review is now a recognized target in the pipeline, but still in the source-discovery phase rather than the full scrape-and-normalize phase. The main accomplishment so far is establishing the right early-stage workflow and constraints for handling it carefully.