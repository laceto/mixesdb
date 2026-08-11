"""Scraper for MixesDB (mixesdb.com) search results.

Uses the MediaWiki action API (/w/api.php) rather than parsing the search
results page HTML, since that page renders its results client-side via
JavaScript and has nothing to parse server-side.

Usage:
    python mixesdb_scraper.py hawtin
    python mixesdb_scraper.py "richie hawtin" --limit 50 --out results.csv
"""

import argparse
import csv
import sys
import time
import urllib.parse
import urllib.request
import json

# Windows consoles often use a legacy codepage (e.g. CP850) that can't encode
# accented characters common in mix titles (e.g. "Sven Väth"), which raises
# UnicodeEncodeError on print(). Force UTF-8 with a safe fallback. Not all
# stdout streams support reconfigure() (e.g. Jupyter's), so this is best-effort.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

API_URL = "https://www.mixesdb.com/w/api.php"
BASE_PAGE_URL = "https://www.mixesdb.com/w/"
USER_AGENT = "Mozilla/5.0 (compatible; mixesdb-scraper/1.0)"
MAX_PER_REQUEST = 50  # MediaWiki API srlimit cap for anonymous users


def title_to_url(title: str) -> str:
    """Reproduce MediaWiki's title -> URL mapping (spaces -> underscores, percent-encoded)."""
    return BASE_PAGE_URL + urllib.parse.quote(title.replace(" ", "_"), safe="/:@,()!'&+")


def matches_query(title: str, query: str) -> bool:
    """True only if every word of the query literally appears in the page title.

    MediaWiki's search is relevance-based, not a strict substring match: it can
    return pages that only mention the query words somewhere in the page body
    (e.g. as a track credit in a tracklist) rather than in the title/lineup.
    Restricting to the title keeps only mixes where the query is actually part
    of the mix's own name (e.g. the performing artist).
    """
    title_lower = title.lower()
    return all(word in title_lower for word in query.lower().split())


def search(query: str, limit: int = 20, namespace: int = 0, strict: bool = True) -> list[dict]:
    """Search MixesDB and return a list of {title, url, snippet, timestamp} dicts.

    When strict=True (default), results that don't literally contain every word
    of the query (in title or snippet) are dropped, and fetching continues until
    `limit` matching results are collected or the search is exhausted.
    """
    results = []
    offset = 0

    while len(results) < limit:
        batch_limit = MAX_PER_REQUEST
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srnamespace": namespace,
            "srlimit": batch_limit,
            "sroffset": offset,
            "format": "json",
        }
        url = f"{API_URL}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        hits = data.get("query", {}).get("search", [])
        if not hits:
            break

        for hit in hits:
            title = hit["title"]
            snippet = strip_html(hit.get("snippet", ""))

            if strict and not matches_query(title, query):
                continue

            results.append(
                {
                    "title": title,
                    "url": title_to_url(title),
                    "snippet": snippet,
                    "timestamp": hit.get("timestamp", ""),
                }
            )
            if len(results) >= limit:
                break

        cont = data.get("continue", {}).get("sroffset")
        if cont is None:
            break
        offset = cont
        time.sleep(0.2)  # be polite

    return results[:limit]


def strip_html(text: str) -> str:
    import re

    return re.sub(r"<[^>]+>", "", text).replace("&nbsp;", " ").strip()


def main():
    parser = argparse.ArgumentParser(description="Search MixesDB and list matching mix page URLs.")
    parser.add_argument("query", help="Search term, e.g. 'hawtin'")
    parser.add_argument("--limit", type=int, default=20, help="Max number of results (default: 20)")
    parser.add_argument("--out", help="Optional path to write results as CSV")
    parser.add_argument(
        "--no-filter",
        action="store_true",
        help="Keep MediaWiki's raw relevance results even if they don't literally contain the search word(s)",
    )
    args = parser.parse_args()

    results = search(args.query, limit=args.limit, strict=not args.no_filter)

    if not results:
        print(f"No results for '{args.query}'.")
        return

    for i, r in enumerate(results, 1):
        print(f"{i}. {r['title']}\n   {r['url']}")

    if args.out:
        with open(args.out, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=["title", "url", "snippet", "timestamp"])
            writer.writeheader()
            writer.writerows(results)
        print(f"\nSaved {len(results)} results to {args.out}")


if __name__ == "__main__":
    main()
