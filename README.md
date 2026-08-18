# mixesdb

Scraper toolkit for [MixesDB](https://www.mixesdb.com/) (a MediaWiki-based DJ
tracklist archive). Instead of parsing HTML — the site's search page renders
results client-side via JavaScript and has nothing to parse server-side —
everything here talks directly to the underlying MediaWiki `action=api.php`
and `action=raw` endpoints.

## Setup

```
python -m venv venv
venv\Scripts\activate                # PowerShell: venv\Scripts\Activate.ps1
pip install -e .                     # installs the `mixesdb` package (stdlib-only, no deps)
pip install jupyter pandas openpyxl  # only needed for the notebook
```

The `mixesdb` package is standard-library only. `pip install -e .` isn't
required to run the three CLI scripts directly from this directory (Python
puts a script's own directory on `sys.path`, and they import their sibling
`mixesdb/` package the same way), but it makes `import mixesdb` work from
anywhere else and is what the test suite (`pip install -e ".[dev]"; pytest`)
relies on.

## Package (`mixesdb/`)

The actual scraping/parsing logic lives in the `mixesdb` package; the three
CLI scripts and the notebook are thin, script-specific wrappers around it.

```
mixesdb/
├── __init__.py      # public API re-exports
├── _shared.py        # API_URL / BASE_PAGE_URL / USER_AGENT / title_to_url()
├── search.py          # search(), matches_query(), strip_html()
├── category.py        # list_category_members(), url_to_category_title()
└── tracklist.py        # get_tracklist(), parse_tracklist(), clean_wikitext(), ...
```

```python
from mixesdb import search, get_tracklist, list_category_members

results = search("richie hawtin", limit=50)
tracks = get_tracklist(results[0]["url"])
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
  Shared by `search` and `category`.
- `list_category_members(category: str, limit: int | None = None) -> list[dict]`
  Returns `{title, url}` dicts for every page in a MixesDB category, e.g.
  [`Category:Richie_Hawtin`](https://www.mixesdb.com/w/Category:Richie_Hawtin)
  (subcategories excluded via `cmtype=page`). Paginates via `cmcontinue`,
  500 per request, sleeping 0.2s between pages.
- `url_to_category_title(value: str) -> str`
  Accepts either a full category URL or a bare `"Category:Name"` string.
- `get_tracklist(url: str) -> list[dict]`
  Fetches a mix page's raw wikitext (`action=raw`) and returns
  `{part, position, timestamp, artist, title, raw}` dicts, one per track.
  Handles pages split into parts/sets (`;Part 1`, `;Part 2`, ...),
  `[hh:mm]`-style timestamps, and strips wiki markup (`[[links]]`,
  `{{templates}}`, `''italics''`). `artist`/`title` are a best-effort split
  of each line on the first ` - `/` – `/` — ` separator; `raw` always holds
  the full cleaned line as a fallback. Returns `[]` if the page has no
  tracklist section.
- `url_to_title(url: str)` / `fetch_raw_wikitext(title: str)` / `parse_tracklist(wikitext: str)`
  Lower-level pieces `get_tracklist()` composes, exposed for reuse.

## CLI scripts

Each script below is a thin wrapper: it parses CLI args, calls into
`mixesdb`, and writes the result to CSV. The underlying functions are
described in [Package (`mixesdb/`)](#package-mixesdb) above.

### `mixesdb_scraper.py` — full-text search

```
python mixesdb_scraper.py hawtin
python mixesdb_scraper.py "richie hawtin" --limit 50 --out results.csv
python mixesdb_scraper.py "richie hawtin" --limit 50 --out results.csv --no-filter
```

CSV output columns: `title, url, snippet, timestamp`.

### `mixesdb_category.py` — list all pages in a category

```
python mixesdb_category.py "https://www.mixesdb.com/w/Category:Richie_Hawtin"
python mixesdb_category.py "Category:Richie Hawtin" --limit 50 --out category.csv
```

CSV output columns: `title, url`.

### `mixesdb_tracklist.py` — scrape one mix's tracklist

```
python mixesdb_tracklist.py "https://www.mixesdb.com/w/2006-08-16_-_Richie_Hawtin_@_Cocorico,_Riccione"
python mixesdb_tracklist.py "<url>" --out tracklist.csv
```

CSV output columns: `part, position, timestamp, artist, title, raw`.

### `mixesdb_search_tracklists.ipynb` — interactive search → tracklists

Imports `search()` and `get_tracklist()` directly from the `mixesdb` package
(no duplicated logic). Prompts for a search word, finds matching mixes
(title-only match), fetches and prints the tracklist for each, and optionally
saves every mix's tracklist to its own sheet in a single
`<query>_tracklists.xlsx` workbook (sheet name derived from the mix title,
sanitized/truncated/deduplicated to fit Excel's 31-character sheet-name
limit) with columns `part, position, timestamp, artist, title, raw`.

A `REQUEST_DELAY = 0.5` pause runs between each per-mix tracklist fetch
(`max_mixes` controls how many matching mixes it fetches, default 20) so a
broad search doesn't fire many rapid-fire requests at the server.

Run with the venv's kernel selected: `jupyter notebook mixesdb_search_tracklists.ipynb`.

## Project structure

```
mixesdb/                          # the library — search, category, tracklist logic
├── __init__.py
├── _shared.py
├── search.py
├── category.py
└── tracklist.py
mixesdb_scraper.py                # CLI: full-text search
mixesdb_category.py               # CLI: list category members
mixesdb_tracklist.py              # CLI: scrape one mix's tracklist
mixesdb_search_tracklists.ipynb   # notebook: interactive search → tracklists (XLSX output)
tests/                            # pytest suite for the pure-logic functions
data/                             # generated CSV/XLSX output (gitignored)
pyproject.toml
requirements.txt
README.md
```

## Notes

- The three CLI scripts write CSVs as `utf-8-sig` (UTF-8 + BOM) so Excel opens
  accented characters (e.g. "Sven Väth") correctly, and force UTF-8 on stdout
  with `errors="replace"` so printing them doesn't crash on Windows consoles
  running a legacy codepage (e.g. CP850). The stdout reconfiguration is
  wrapped in `try/except AttributeError` since not all stdout streams support
  `.reconfigure()` (notably Jupyter's). It lives only in the CLI scripts, not
  in the `mixesdb` package itself, since the package's functions never print —
  importing `mixesdb` (e.g. from the notebook) never touches stdout.
- All MediaWiki API/raw requests send a custom `User-Agent` and pause briefly
  between paginated batches — be considerate of the server if you raise
  `--limit` significantly.
- `data/` is the gitignored home for generated output — pass e.g.
  `--out data/results.csv` to the CLI scripts to save there directly. Both the
  CLI scripts and the notebook default to writing into the current directory
  unless you give them a `data/`-prefixed path.
