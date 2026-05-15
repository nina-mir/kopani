# Observations on scrape_evergreen_piece_v0_2_1.py

- first piece ```  {
            "title": "[DAS VIDEOSPIEL] Beautiful Suffering",
            "url": "http://evergreenreview.com/read/das-videospiel-beautiful-suffering/",
            "author": "Alice Maynwaring",
            "type": ""
        }'''
The name for this piece is wrongly recorded in the scraped json which is odd, since the name is already provided to the scraper as shown in the above snippet. 

current scraped JSON display:```"author": "Beautiful Suffering: How I Created a Larp to Drive People Insane",
    "visual_artist": null
  },
  "authors_raw": [
    {
      "display_name": "Beautiful Suffering: How I Created a Larp to Drive People Insane",
      "author_url": null
    }
  ],```

  Author's bio is simply wrong. The fact it does not contain the author's name should be telling.``` 
  "derived": {
    "author_bio_raw": "Fielding’s Hollow\nis an intense, paranoiac live-action role-playing experience for sixteen players, set in a fictional mining town in 1890s New England.",
    "visual_artist_bio_raw": null
  },```

  It appears that this specific piece has several h4 tags, 9 h4 tags. 
```
for (const elem of h4){
    console.log(elem.textContent)
}
 Alice Maynwaring
 ***
 Following your intuition
 Capturing the sacred
 Crafting a character
 Structure & Artificial Laws
 Driving people insane
 The shard of glass
 Alice Maynwaring
```
The last h4 tag is the author's name which is promptly followed by the author's bio. This pattern is seen across Evergreen pieces analyzed so far. Please make a note of this matter. It has been clearly stated to you on multiple occassions. 

## Since the Author's name is provided in the issue_json file, it is paramount to tak advantage of this matter. 

In the document evergreen_findings_v0.md provided in this Space's files to you, it was mentioned:

> - author's bio paragraph can be found right after an h4 tag containing the authro;s name like this:

The author's bio is always at the bottom of the piece before the footer and right after the text body of the piece ends. 

The anlyzed piece here has no visual artist info mentioned, so I won't be making any points about that. 




- second piece ```   {
            "title": "D.C. Repro",
            "url": "http://evergreenreview.com/read/dc-repro/",
            "author": "Marc Ganzglass",
            "type": ""
        }
        '''

The scraped data from this piece is acceptable. 


- third piece ```{
            "title": "From “more than anything”",
            "url": "http://evergreenreview.com/more-than-anything-africa-wayne/",
            "author": "Africa Wayne",
            "type": ""
        }
```
The scraped data from this piece is acceptable. 
How do you decide if this is False or True? -->  "head_metadata_trusted": false


- fourth piece 
```{
            "title": "HEXALOGY OF HAGSPLOITATION: Hepzibah 11.21.25",
            "url": "http://evergreenreview.com/read/hexalogy-of-hagsploitation/",
            "author": "Sibyl Kempson",
            "type": ""
        }
```
The scraped data from this piece is acceptable. 
How do you decide if this is False or True? --> "head_metadata_trusted": true


- fifth piece ```{
            "title": "Son of a Natural Man",
            "url": "http://evergreenreview.com/read/son-of-a-natural-man/",
            "author": "Reggie Scott Young",
            "type": ""
        }
```
The scraped data from this piece is acceptable. 


