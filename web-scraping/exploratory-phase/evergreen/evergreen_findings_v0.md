# Evergreen Review Journal
### issue Fall/Winter 2025

## Data already scraped regarding the issue
```json
    "issue_url": "http://evergreenreview.com/fw25/",
    "issue_label": "Fall / Winter 2025-2026",
    "issue_number": null,
    "issue_date": "Fall / Winter 2025-2026",
    "piece_count": 40,
```

## Piece 1
### Data already available
```json
{
    "title": "From “more than anything”",
    "url": "http://evergreenreview.com/more-than-anything-africa-wayne/",
    "author": "Africa Wayne",
    "type": ""
}
```
### problem 
    - The info in the \<head> do not correspond to the piece. 
    - For example, the author's info and piece's keywords are for another piece. 
    - So, to trust the info in the \<head>, the name of the piece's author must be seen else that info is not reliable and a "note" need to be generated asking for "manual review due to lack of author's info in the head tag" or some such.
    - for this specific piece the info in the head are:
    <meta name="description" content="&quot;Robbie gave you a blush pink crystal&quot; and Other Poems by Marisa Crawford | Art by Gabrielle Garland | Evergreen Review">
    <meta name="keywords" content="Poetry, Marisa Crawford, Gabrielle Garland">
    the above info are for another piece in the same issue!!

- title is mentioned in the title tag:```<title>From “more than anything” – Evergreen Review</title>```
- canonical url can be found here: 
```<link rel="canonical" href="http://evergreenreview.com/more-than-anything-africa-wayne/">```  OR 
```<meta property="og:title" content="From &quot;more than anything&quot;">```  OR ```<meta itemprop="name" content="From &quot;more than anything&quot;">``` OR ```<meta itemprop="headline" content="From &quot;more than anything&quot;">```

- h1 tag has info on the piece's title: ```<h1 class="intro-title">From “more than anything”</h1>```
- author's name is mentioned in a h3 tag: ```<h3>Africa Wayne</h3>```
- author's name is followed by the name of the artist that their art is used in the piece for visuals:
```<p>Art by Maya Deren</p>```

--  ```
    <div class="column_attr clearfix" style="">
        <h3>Africa Wayne</h3>
        <p>Art by Maya Deren</p>
    </div>
    ```
- content of this poem is entirely within one pargraph tag
```
<p>*<br>
to wait<br>
for peace <br>
in times <br>
of force<br>
to cut oneself<br>
a treaty<br>
<br>
 <br>
<br>
<br>
<br>
<br>
<br>
<br>
<br>
*<br>
unreliable<br>
your tales are tall<br>
the mental lift<br>
a pilot<br>
<br>
 <br>
<br>
<br>
<br>
<br>
<br>
<br>
*<br>
not will<br>
but wiring<br>
the way we blend<br>
a patch<br>
between the upgrades<br>
a newer true is coming<br>
<br>
 <br>
<br>
<br>
<br>
<br>
<br>
<br>
<br>
*<br>
fears laid thick<br>
not mined   a fallacy<br>
between the hateful weight<br>
a kindness <br>
<br>
 <br>
<br>
<br>
<br>
<br>
<br>
<br>
*<br>
a rat for the water<br>
all sweetness and stick<br>
shamed by the want of it<br>
wanting the shame of it<br>
clearing a path<br>
the new maze<br>
<br>
 <br>
<br>
<br>
<br>
<br>
<br>
<br>
*<br>
knowing a thing<br>
isn’t owning it<br>
to call a child inner<br>
question of location<br>
pinned in sections<br>
stranded worm<br>
<br>
 <br>
<br>
<br>
<br>
<br>
<br>
<br>
<br>
*<br>
in trance<br>
an entrance &nbsp; &nbsp; activated<br>
<br>
 <br>
<br>
<br>
<br>
<br>
<br>
<br>
*<br>
ample<br>
the end is nowhere <br>
edgeless the instant closed<br>
<br>
 <br>
<br>
<br>
<br>
<br>
<br>
<br>
*<br>
gesture a gift <br>
in telling it<br>
some sky to see<br>
new awning<br>
<br>
 <br>
<br>
<br>
<br>
<br>
<br>
*<br>
as if the dead deer<br>
was not enough to signal <br>
distance<br>
fear marks <br>
the edge of sight<br>
and clearly <br>
no two things <br>
resemble fire</p>
```
- issue specs can be found here: ``` <strong>
Fall / Winter 2025
</strong>```

- author's bio paragraph can be found right after an h4 tag containing the authro;s name like this:
```<h4>Africa Wayne</h4>
    <p>Africa Wayne is the author of tiny pony and the editor of <em>Dürer in the Window: Reflexions on Art</em>, by Barbara Guest. Like echoes reverberating, her poems amplify an interior dialogue while engaging with themes of isolation and retrieval. Her poetry is published in <em>Aufgabe</em> and <em>How2</em>; a new collection is forthcoming. 
</p>
```
- bio for the visual artist whose work is used in the piece follows similar structure:
```<h4>Maya Deren</h4>
    <p>Maya Deren, born Eleonora Solomonovna Derenkovskaya (1917-1961) was a Russian American experimental filmmaker and part of the 1940s and 50s avant-garde. She was also a choreographer, dancer, film theorist, poet, lecturer, writer, and photographer. <em><a href="https://en.wikipedia.org/wiki/Meshes_of_the_Afternoon" target="_blank">Meshes of the Afternoon</a></em> (1943) is an experimental silent short film written, edited, directed by, and starring Maya Deren and Alexandr Hackenschmied (her husband and the film's cinematographer). In 1990, the film was selected for preservation in the United States National Film Registry by the <a href="https://www.loc.gov/item/91731958/" target="_blank">Library of Congress</a> for its cultural and historical significance. 
    </p>
```

## Piece 2
- data already obtained: ```
{
            "title": "Silent Upon a Peak",
            "url": "http://evergreenreview.com/read/silent-upon-a-peak/",
            "author": "Belén Fernández",
            "type": ""
        }
        ```
- This piece is an essay but it is not mentioned as a category in this piece's HTML page
- piece title can be found here: ``` <h1 class="intro-title">Silent Upon a Peak</h1>```
OR maybe from the title tag ```<title>Silent Upon a Peak – Evergreen Review</title>```
OR ```<meta property="og:title" content="Silent Upon a Peak">``` OR ```<meta itemprop="name" content="Silent Upon a Peak">``` OR ```<meta itemprop="headline" content="Silent Upon a Peak">```

- canonical url ```<link rel="canonical" href="http://evergreenreview.com/read/silent-upon-a-peak/">```

- this meta tag has amazing info: ```<meta name="description" content="Silent Upon a Peak by Belén Fernández | Art by Susan Hamburger">``` differentiating the writer from the visual artist whose work is used in the piece.

- the following keywords are extremely helpful in identifying the type of the content_type. In this case, nonfiction is the data point we want! ```<meta name="keywords" content="Belén Fernández, Susan Hamburger, Nonfiction, Darién Gap, Darien Gap, Biography and Memoir, Caribbean Studies, General Interest, History, Human Rights, Latin American Studies, Political Science">``` Moreover, the keywords can be used in the piece's keywords to be used in tagging the piece later!!

- The Author's name and the Visual Artists whose work is used in the piece for visual purpose can be found in here:
```
<div class="column_attr clearfix" style="">
    <h3>Belén Fernández</h3>
    <p>Art by Susan Hamburger</p>
</div>
```

- Piece issue specs: ```<strong>
Fall / Winter 2025
</strong>```


- text content: It is very hard to provide a pattern for the text content since it is in p tags across multiple adjacent div elements with no pattern seperated with images. However, it appears all the text within paragraph elements from the 
"Art by <artist name>" to the Piece issue specs is the text content. It also appears the paragraphs that follows the piece specs are the author's bio and the artist's bio. It is not clear if all the pieces will have an artist in them or not. 

- Notable: THe name of the writer is within h4 tags before being followins by the author's bio:
```<h4>Belén Fernández</h4>
<p>Belén Fernández is an opinion columnist for <em>Al Jazeera</em>, and her articles have appeared in the <em>New York Times</em>, the <em>London Review of Books</em> blog, and <em>The Baffler</em>, among other outlets. Previous books include <em>Inside Siglo XXI: Locked Up in Mexico’s Largest Immigration Detention Center</em>, <em>Exile: Rejecting America and Finding the World</em>, and <em>The Imperial Messenger: Thomas Friedman at Work</em>.
</p>
```

- after the writer's name and bio, the name of the artist is mentioned again within h4 tag followed by their bio:
```
<h4>Susan Hamburger</h4>
<p><a href="https://www.susanhamburger.net/" target="_blank">Susan Hamburger</a> (BA Brandeis University; MFA Rutgers; MA in Art Education CCNY) lives and works in Brooklyn, NY. Her many honors include residencies, fellowships, and awards from The Women’s Studio Workshop (Anita Wetzel Residency); Dieu Donné Papermill; Wassaic Project Print Studio; The National Academy Abbey Mural Workshop; Aljira; Ucross Foundation; Jentel Foundation; Saltonstall Foundation; The Millay Colony; PS122; Abrons Art Center; and Chashama. Her most recent solo show "Near Enemies" is on view at <a href="https://www.asyageisberggallery.com/index.php/exhibitions" target="_blank">Asya Geisberg Gallery in New York</a> from  Oct. 24 through Dec. 20, 2025. Previous solo exhibitions were held at The Wassaic Project, Schroeder Romero &amp; Shredder, Visual Arts Center of New Jersey, Tomasulo Gallery at Union County College, Cheryl McGinnis Gallery. among others. Her work has been included in group exhibitions at the Brooklyn Museum of Art, Urban Glass, Mixed Greens, Pierogi Gallery, 601Artspace, Pelham Art Center, and No Longer Empty.
</p>
```


