# Observations on scrape_evergreen_piece_v0_2_2.py

- first piece '''{
            "title": "Witch Hunts",
            "url": "http://evergreenreview.com/read/witch-hunts/",
            "author": "Terese Svoboda",
            "type": ""
        },
'''
pretty good!

- second piece ``` {
            "title": "Pizza Space-Time",
            "url": "http://evergreenreview.com/read/pizza-space-time/",
            "author": "Gabriel Abrantes, João Marçal",
            "type": ""
        },
```
excellent work. notably the following notes are correct since this piece is a bit hard to decipher and a manual review is the right call for sure!
"notes": [
      "top_author_mismatch_issue_json_vs_page",
      "manual_review_head_metadata_untrusted"
    ]
My only suggestion is to add a simple "manual_review" to the notes array in addition to whatever else is added, so when I run diagnostic, it is easier to get this. 

- third piece ''' {
            "title": "An Interview with Sahar Delijani",
            "url": "http://evergreenreview.com/read/an-interview-with-sahar-delijani/",
            "author": "Porochista Khakpour, Sahar Delijani",
            "type": "interview"
        } '''
      
This is in interview piece and we can safely assume it has two writers because the given author's value from the json says so!
More importantly, the authors' names are seperated with a comma in the issue json, so perhaps, in such cases, we could assume there are more than one writer. As such, writer's bio aslo becomes an array of two author's bio. 

for emxaple the following values could be "author_bio_raw": [bio_1, bio_2]

"derived": {
    "author_bio_raw": "Sahar Delijani is the author of\nChildren of the Jacaranda Tree\n, an internationally acclaimed novel, translated into thirty-two languages and published in more than seventy-five countries. Delijani’s writing has appeared in\nLiterary Hub\n,\nMcSweeney’s Quarterly Concern\n,\nBOMB Magazine\n,\nThe Kenyon Review\n,\nKweli Journal\n,\nThe Bellevue Review\nand many more. She is the recipient of the 2023 de Groot Foundation Courage to Write Grant, the 2023 Society of Authors and Author’s Foundation Grant, and of fellowships at Tin House, Art Omi: Writers, Hedgebrook and Monson Arts. Her work has furthermore been longlisted for the 2024 NYC Café Royal Cultural Foundation, the 2022 Granum Foundation Prize, and nominated several times for the Pushcart Prize and the Best American Essay Series. Born in Iran, Delijani grew up in California and lived for many years in Turin, Italy. She currently lives in New York City.",
    "visual_artist_bio_raw": null
  },

I like the following note but again I would ask for a simple "manual_review" flag in addition to this as well.
"notes": [
      "top_author_mismatch_issue_json_vs_page"
    ]

For the following "authors_raw": [
    {
      "display_name": "Porochista Khakpour, Sahar Delijani",
      "author_url": null
    }
  ],

we could two writers easily. 

In general it is good and a bit of improvement would make it more resilient to unstructured pieces that we may stuble upon.

- fourth piece ```{
            "title": "Arewa Boys",
            "url": "http://evergreenreview.com/read/arewa-boys/",
            "author": "Hussani Abdulrahim",
            "type": ""
        },
```
This is great! 

- fifth piece ```      {
            "title": "Adult and Other Poems",
            "url": "http://evergreenreview.com/read/adult-and-other-poems/",
            "author": "Thomas Sayers Ellis",
            "type": "poems"
        },
```
this is great!

