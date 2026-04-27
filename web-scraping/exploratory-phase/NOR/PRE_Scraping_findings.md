# Exploraty Webscraping phase

## Current Issue Page

> TASK : On the issue page, identify the repeating card or list element that links to each piece, and note which fields are present there: piece URL, title, subtitle, author name, issue label, date, teaser, featured image, and category. Also inspect whether the page contains structured data like JSON-LD, article:published_time, og:title, author meta tags, or WordPress classes that can give you more stable extraction than brittle CSS chains. 

PAGE TYPE:                  issue
URL:                        https://www.neworleansreview.org/issue-53-summer-2025/
TITLE SELECTOR:             /html/head/title
SUBTITLE SELECTOR:          None found
AUTHOR NAME SELECTOR:       
AUTHOR URL SELECTOR:
DATE SELECTOR:
BIO SELECTOR:
ISSUE SELECTOR:
THEME SELECTOR:
JSON-LD PRESENT?: yes/no
NOTES:
HTML SNIPPET:


# New Orleans Review — Issue 53 Summer 2025 inspection

## Issue page
URL: https://www.neworleansreview.org/issue-53-summer-2025/

### Observed section groups
- Art
- Poetry
- Fiction
- Nonfiction
- Interviews

### Repeating link block selector
- Container selector:
- Link selector:
- Title selector:
- Author selector:
- Subtitle selector:
- Category/section selector:
- Any issue-level theme text selector:
- Notes:

## Piece link inventory

The element right after a <h3> tag is a <p> tag that nexts several links to pieces.

Example: /html/body/div/div/div[1]/div/main/article/div/p[13]/a[2]

The text content of <h3> tags are Art, Intrviews, Fiction, Poetry and Nonfiction in that order. 

example of an <h3> tag: /html/body/div/div/div[1]/div/main/article/div/h3[1]

Example of a <p> tag, sibling to an <h3> tag: /html/body/div/div/div[1]/div/main/article/div/p[13]

Example of a <a> tag for a piece: /html/body/div/div/div[1]/div/main/article/div/p[11]/a[1]

As can be seen in this HTML example of a fictions piece, 
<a href="https://www.neworleansreview.org/throat-fish/">“throat fish” by Winston Turnage</a>
, name of the write is within the text content preceded by the term "by."


# NOR issue page inspection

issue_url: https://www.neworleansreview.org/issue-53-summer-2025/

issue_title: Issue 53 : Summer 2025

journal: New Orleans Review

| section | order_in_section | piece_url | link_text_raw | parse_guess | notes |
|---|---:|---|---|---|---|
| Fiction | 1 | https://www.neworleansreview.org/inheritance/ | “Inheritance” by Kasey Buckley | title=Inheritance; author=Kasey Buckley | clean pattern |
| Fiction | 2 | https://www.neworleansreview.org/throat-fish/ | “throat fish” by Winston Turnage | title=throat fish; author=Winston Turnage | clean pattern |
| Poetry | 1 | https://www.neworleansreview.org/cum-rag-relapse/ | “Cum Rag” & “relapse” by Alexa Doran | multiple titles; one author | multi-piece row |
| Interviews | 1 | ... | Amel Khalil by Briana Bhola | subject/interview title ambiguous | interview pattern |


## Fiction Piece --> Cetacean Stranding by Madeleine Hollis

- fiction title matches the webpage's <title> element : <title>Cetacean Stranding</title>
- canonical link is <link rel="canonical" href="https://www.neworleansreview.org/cetacean-stranding/">
- breadcrumbs class exists and has information like the following 

<div class="breadcrumb" itemscope="" itemtype="https://schema.org/BreadcrumbList">You are here: <span class="breadcrumb-link-wrap" itemprop="itemListElement" itemscope="" itemtype="https://schema.org/ListItem"><a class="breadcrumb-link" href="https://www.neworleansreview.org/" itemprop="item"><span class="breadcrumb-link-text-wrap" itemprop="name">Home</span></a><meta itemprop="position" content="1"></span> <span aria-label="breadcrumb separator">/</span> <span class="breadcrumb-link-wrap" itemprop="itemListElement" itemscope="" itemtype="https://schema.org/ListItem"><a class="breadcrumb-link" href="https://www.neworleansreview.org/category/53/" itemprop="item"><span class="breadcrumb-link-text-wrap" itemprop="name">53</span></a><meta itemprop="position" content="2"></span> <span aria-label="breadcrumb separator">/</span> Cetacean Stranding</div>

for this fictions piece it is--> You are here: Home / 53 / Cetacean Stranding

- visible title: <h1 class="entry-title" itemprop="headline">Cetacean Stranding</h1>
- displayed author's name:  <a href="https://www.neworleansreview.org/writer/madeleine-hollis/">Madeleine Hollis</a>
it appears the hrefvalue for this anchor tag contains the path "/writer/" which links to the author's page which may or may not contain the list of all this writer's publications in this journal
- the content of this short fiction is the text content of this element: <div class="entry-content" itemprop="text">

- author's bio is here: <hr class="wp-block-separator has-alpha-channel-opacity">
<p>Madeleine Hollis is a New Orleans based writer whose previous work appears in Ellipses: A Journal of Art, Ideas, and Literature, and New York Moves Magazine. She has a keen interest in the strange and magical details of everyday life, which she hopes to explore further as she moves towards an MFA.</p>


## Poetry with Multiple titles
> My mother tells me not to walk alone in the forest, so I drop my location on a pin. & Before He Duct-Taped his Million-Dollar Banana to a Wall, Mauritzio Cattelan Made “Daddy, Daddy:”  by Lizzy Ke Polishan

URL : https://www.neworleansreview.org/my-mother-tells-me-not-to-walk-alone-in-the-forest-so-i-drop-my-location-on-a-pin-before-he-duct-taped-his-million-dollar-banana-to-a-wall-mauritzio-cattelan-made-daddy-daddy/

Visible Title: My mother tells me not to walk alone in the forest, so I drop my location on a pin. & Before He Duct-Taped his Million-Dollar Banana to a Wall, Mauritzio Cattelan Made “Daddy, Daddy:”

Main Title HTML: <h1 class="entry-title" itemprop="headline">My mother tells me not to walk alone in the forest, so I drop my location on a pin. &amp; Before He Duct-Taped his Million-Dollar Banana to a Wall, Mauritzio Cattelan Made “Daddy, Daddy:”</h1>

Single poem title: <h3>My mother tells me not to walk alone<br>&nbsp; &nbsp; &nbsp; &nbsp; &nbsp; in the forest, so I drop her my location on a pin.</h3>

Single poem HTML: <h3>Before He Duct-Taped his Million-Dollar Banana to a Wall, Maurizio Cattelan Made “Daddy, Daddy:”</h3>

Visible Author: Lizzy Ke Polishan 

Author's HTML: <header class="entry-header"><h1 class="entry-title" itemprop="headline">My mother tells me not to walk alone in the forest, so I drop my location on a pin. &amp; Before He Duct-Taped his Million-Dollar Banana to a Wall, Mauritzio Cattelan Made “Daddy, Daddy:”</h1>
<p class="entry-meta"><span class="entry-categories"><a href="https://www.neworleansreview.org/category/53/" rel="category tag">53</a>, <a href="https://www.neworleansreview.org/category/new-issue/new-poetry/" rel="category tag">New Poetry</a></span> by <a href="https://www.neworleansreview.org/writer/lizzy-ke-polishan/">Lizzy Ke Polishan</a> </p></header>

Notes: There are two poems on this page seperated by a horizontal line. Each poem has a title before the text of the poem. 

Author bio: YES

NOte about Author's bio: It seems to be last <p> in the <main> tag.  

## Interview
> Lisa Sanaye Dring by Marigny Beter

URL : https://www.neworleansreview.org/lisa-dring/

Visible title: Lisa Dring

-- The <header> element contains information includin a h1 tag of the title and the intervier's name

<header class="entry-header"><h1 class="entry-title" itemprop="headline">Lisa Dring</h1>
<p class="entry-meta"><span class="entry-categories"><a href="https://www.neworleansreview.org/category/53/" rel="category tag">53</a>, <a href="https://www.neworleansreview.org/category/new-issue/new-interview/" rel="category tag">New Interview</a></span> by <a href="https://www.neworleansreview.org/writer/marigny-beter/">Marigny Beter</a> </p></header>

-- a div elment with this xpath :  /html/body/div/div/div[1]/div/main/article/div/div[1]
contains the interviewee's bio and achievement 
HTML code <div>
<div><span style="font-size: small;"><span id="m_-5109676909930193697m_-4360298989843987182m_7058651091991625737gmail-docs-internal-guid-8029764c-7fff-4139-d072-2dc2b5524f85">Lisa Sanaye Dring is a writer and director from Hilo, Hawaii and Reno, Nevada. Her play SUMO was produced by La Jolla Playhouse and Ma-Yi Theater Company in 2023 and by The Public with Ma-Yi in 2025. It was nominated for 5 Lortel Awards (including Outstanding New Play) and 3 Drama Desk Awards. They were the 2024 Tow Foundation Writer-in-Residence with Ma-Yi and her play Kairos recently received a Rolling World Premiere with NNPN. Lisa has won an Edgerton Award, Broadway World Award, and a PLAY LA Stage Raw/Humanitas Prize. They’ve been a finalist for the Relentless Award, O’Neill Playwrights’ Conference (2x), Seven Devils Playwrights Conference, and a 3x finalist (one honorable mention) for the Bay Area Playwrights Festival. Fellowships include MacDowell, Blue Mountain Center and Yaddo. She received an Emmy nomination for </span><span id="m_-5109676909930193697m_-4360298989843987182m_7058651091991625737gmail-docs-internal-guid-8029764c-7fff-4139-d072-2dc2b5524f85">Outstanding Interactive Programming for </span><span id="m_-5109676909930193697m_-4360298989843987182m_7058651091991625737gmail-docs-internal-guid-8029764c-7fff-4139-d072-2dc2b5524f85">co-writing and co-directing a project with Matt Hill. </span></span></div>
</div>

-- there is only one h1 tag and one title on this page

-- the interviewer's bio is the last paragraph tag in the main element that contains the entire interview text with the following xpath
/html/body/div/div/div[1]/div/main/article/div/p[42]

## nonfiction essay 
> “A Clear Day for Bombs” by Jean McDonough 

URL : https://www.neworleansreview.org/a-clear-day-for-bombs/

-- the header element contain the main title and info about the issue number and author like the following HTML code:
<header class="entry-header"><h1 class="entry-title" itemprop="headline">A Clear Day for Bombs</h1>
<p class="entry-meta"><span class="entry-categories"><a href="https://www.neworleansreview.org/category/53/" rel="category tag">53</a>, <a href="https://www.neworleansreview.org/category/new-issue/new-essay/" rel="category tag">New Essay</a></span> by <a href="https://www.neworleansreview.org/writer/jean-mcdonough/">Jean McDonough</a> </p></header>

Visible title: A Clear Day for Bombs
Visible author:  Jean McDonough
Author's bio: It is the last p tag in the main html element with this xpath /html/body/div/div/div[1]/div/main/article/div/p[39]


## art piece

URL : https://www.neworleansreview.org/le-feu-brule/

Visible title exists: Le Feu Brûle

> Le Feu Brûle

> header is 53, New Art by Prisca Munkeni Monnier
HTM lcode for header element: <header class="entry-header"><h1 class="entry-title" itemprop="headline">Le Feu Brûle</h1>
<p class="entry-meta"><span class="entry-categories"><a href="https://www.neworleansreview.org/category/53/" rel="category tag">53</a>, <a href="https://www.neworleansreview.org/category/new-issue/new-art/" rel="category tag">New Art</a></span> by <a href="https://www.neworleansreview.org/writer/prisca-munkeni-monnier/">Prisca Munkeni Monnier</a> </p></header>

No artist bio exists.

Note: Artist statement exists. 