# mixesdb

Scraper toolkit for [MixesDB](https://www.mixesdb.com/) (a MediaWiki-based DJ
tracklist archive). Instead of parsing HTML — the site's search page renders
results client-side via JavaScript and has nothing to parse server-side —
everything here talks directly to the underlying MediaWiki `action=api.php`
and `action=raw` endpoints.

## Setup

```
python -m venv venv
venv\Scripts\activate          # PowerShell: venv\Scripts\Activate.ps1
pip install jupyter pandas     # only needed for the notebook
```

The three `.py` scripts use only the standard library — no dependencies
required to run them directly.

## Modules

### `mixesdb_scraper.py` — full-text search

Searches MixesDB via `list=search` and returns matching mix pages.

```
python mixesdb_scraper.py hawtin
python mixesdb_scraper.py "richie hawtin" --limit 50 --out results.csv
python mixesdb_scraper.py "richie hawtin" --limit 50 --out results.csv --no-filter
```

- `search(query: str, limit: int = 20, namespace: int = 0, strict: bool = True) -> list[dict]`
  Returns `{title, url, snippet, timestamp}` dicts. Paginates automatically
  (50 results per request) until `limit` matching results are collected or
  the search is exhausted, sleeping 0.2s between pages.
- `matches_query(title: str, query: str) -> bool`
  True only if every word of `query` literally appears in `title`. MediaWiki's
  search is relevance-based, not a strict substring match — it can return
  pages that only mention the query word somewhere in the page body (e.g. as
  a track credit inside another artist's tracklist) rather than in the title.
  `search()` applies this filter by default (`strict=True`) so every returned
  row genuinely has the search term(s) in its own title; pass `strict=False`
  (CLI: `--no-filter`) to fall back to MediaWiki's raw relevance ranking.
- `title_to_url(title: str) -> str`
  Reproduces MediaWiki's title→URL mapping (spaces→underscores, percent-encoded).
- CSV output columns: `title, url, snippet, timestamp`.

### `mixesdb_category.py` — list all pages in a category

Enumerates every page in a MixesDB category via `list=categorymembers`, e.g.
[`Category:Richie_Hawtin`](https://www.mixesdb.com/w/Category:Richie_Hawtin).

```
python mixesdb_category.py "https://www.mixesdb.com/w/Category:Richie_Hawtin"
python mixesdb_category.py "Category:Richie Hawtin" --limit 50 --out category.csv
```

- `list_category_members(category: str, limit: int | None = None) -> list[dict]`
  Returns `{title, url}` dicts for every page (subcategories excluded via
  `cmtype=page`). Paginates via `cmcontinue`, 500 per request, sleeping 0.2s
  between pages.
- `url_to_category_title(value: str) -> str`
  Accepts either a full category URL or a bare `"Category:Name"` string.
- CSV output columns: `title, url`.

### `mixesdb_tracklist.py` — scrape one mix's tracklist

Fetches a single mix page's raw wikitext (`action=raw`) and parses the
`== Tracklist ==` section into structured entries.

```
python mixesdb_tracklist.py "https://www.mixesdb.com/w/2006-08-16_-_Richie_Hawtin_@_Cocorico,_Riccione"
python mixesdb_tracklist.py "<url>" --out tracklist.csv
```

- `get_tracklist(url: str) -> list[dict]`
  Returns `{part, position, timestamp, artist, title, raw}` dicts, one per
  track. Handles pages split into parts/sets (`;Part 1`, `;Part 2`, ...),
  `[hh:mm]`-style timestamps, and strips wiki markup (`[[links]]`,
  `{{templates}}`, `''italics''`). `artist`/`title` are a best-effort split
  of each line on the first ` - `/` – `/` — ` separator; `raw` always holds
  the full cleaned line as a fallback. Returns `[]` if the page has no
  tracklist section.
- `url_to_title(url: str)` / `fetch_raw_wikitext(title: str)` / `parse_tracklist(wikitext: str)`
  Lower-level pieces `get_tracklist()` composes, exposed for reuse (e.g. by
  the notebook).
- CSV output columns: `part, position, timestamp, artist, title, raw`.

### `mixesdb_search_tracklists.ipynb` — interactive search → tracklists

Imports `search()` and `get_tracklist()` directly from the two modules above
(no duplicated logic). Prompts for a search word, finds matching mixes
(title-only match), fetches and prints the tracklist for each, and saves the
combined result to `<query>_tracklists.csv` with columns
`mix_title, mix_url, part, position, timestamp, artist, title, raw`.

A `REQUEST_DELAY = 0.5` pause runs between each per-mix tracklist fetch
(`max_mixes` controls how many matching mixes it fetches, default 20) so a
broad search doesn't fire many rapid-fire requests at the server.

Run with the venv's kernel selected: `jupyter notebook mixesdb_search_tracklists.ipynb`.

## Notes

- All three CLI scripts write CSVs as `utf-8-sig` (UTF-8 + BOM) so Excel opens
  accented characters (e.g. "Sven Väth") correctly, and force UTF-8 on stdout
  with `errors="replace"` so printing them doesn't crash on Windows consoles
  running a legacy codepage (e.g. CP850). The stdout reconfiguration is
  wrapped in `try/except AttributeError` since not all stdout streams support
  `.reconfigure()` (notably Jupyter's), which would otherwise break importing
  these modules from the notebook.
- All MediaWiki API/raw requests send a custom `User-Agent` and pause briefly
  between paginated batches — be considerate of the server if you raise
  `--limit` significantly.
