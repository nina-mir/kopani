import sqlite3, json
c = sqlite3.connect("kopani.sqlite").cursor()

# how many Granta pieces now carry keywords vs not
rows = c.execute("""
    SELECT p.ai_keywords_json
    FROM pieces p JOIN journals j ON p.journal_id = j.id
    WHERE j.slug = 'granta'
""").fetchall()

have = sum(1 for (kw,) in rows if kw)
print(f"granta pieces: {len(rows)}, with keywords: {have}, null: {len(rows)-have}")

# spot-check a few
for (kw,) in rows[:5]:
    print(json.loads(kw) if kw else None)

rows = c.execute("""
    SELECT p.slug, p.raw_json
    FROM pieces p JOIN journals j ON p.journal_id = j.id
    WHERE j.slug = 'granta' AND p.ai_keywords_json IS NULL
""").fetchall()
for slug, raw in rows:
    d = json.loads(raw)
    pk = d.get("piece", {}).get("keywords")
    pm = (d.get("page_metadata") or {}).get("keywords")
    print(f"{slug:35s} piece={pk!r}  page_meta={pm!r}")