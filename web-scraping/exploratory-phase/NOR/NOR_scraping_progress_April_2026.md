# New Orleans Review Scraping Progress

## Overview

We have made solid progress on the exploratory scraper for *New Orleans Review*. The current workflow includes discovering piece URLs from issue pages, scraping pieces individually, and outputting one JSON file per piece with the full main text preserved in `content.text`.   

## What has been accomplished

- Built an issue-to-piece discovery workflow so piece URLs can be collected first and scraped in a second step.   
- Established the per-piece JSON output format, with emphasis on preserving the full article or poem text in a dedicated text field.   
- Verified that many standard pieces are scraping correctly, including title, author, link text, main text, and author bio in straightforward cases.    
- Fixed an important parser bug by extending `HEADING_TAGS` to include `h5`, which resolved a multi-poem extraction problem in *New Orleans Review* issue 49.    

## Findings from QA

QA review showed that the scraper performs well on many fiction, essay, and art entries, where fields like `piece.originalurl`, `piece.titledisplay`, `authorsraw`, `derived.authorbioraw`, and `content.text` were marked correct.   The main remaining difficulty is multi-poem pieces, especially when poems are visually separated by `hr` elements and inner poem titles are detected but the poem texts are not split correctly.    

## Known issues

- In some multiple-title poem entries, `content.subworks` captures inner poem titles correctly, but `content.text` does not preserve the full text structure of each poem.    
- In certain cases, part of a poem is incorrectly absorbed into `derived.authorbioraw`.    
- There have also been structural edge cases involving over-capture of author information in multi-poetry pieces, which still require careful handling.   

## Current status

The scraper is already producing useful results for a substantial portion of *New Orleans Review* content, and the main unresolved work is concentrated in edge cases rather than the basic pipeline.       At this point, the project has moved from initial feasibility into targeted refinement of poem-specific and structure-specific parsing behavior.     