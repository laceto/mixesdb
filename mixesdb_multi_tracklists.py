"""CLI: search MixesDB for a list of DJs/queries and fetch every match's tracklist.

Thin wrapper over the mixesdb package's search() and get_tracklist() — loops the
same search -> fetch flow as mixesdb_search_tracklists.ipynb over multiple
queries instead of one, and writes every track from every DJ into a single
long CSV table (one row per track, tagged with which query/DJ it came from).

Usage:
    python mixesdb_multi_tracklists.py
    python mixesdb_multi_tracklists.py "Nick Curly" "Sonja Moonear" --limit 50
    python mixesdb_multi_tracklists.py "Barem" --out data/barem_tracklists.csv
"""

import argparse
import csv
import sys

from mixesdb import get_tracklist, search

# Windows consoles often use a legacy codepage (e.g. CP850) that can't encode
# accented characters common in mix titles (e.g. "Sven Väth"), which raises
# UnicodeEncodeError on print(). Force UTF-8 with a safe fallback. Not all
# stdout streams support reconfigure() (e.g. Jupyter's), so this is best-effort.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass

# The DJ list from mixesdb_search_tracklists.ipynb's query cell, used when no
# queries are given on the command line.
DEFAULT_QUERIES = [
    "Nick Curly",
    "Sonja Moonear",
    "Barem",
    "Karotte",
    "Dan Ghenacia",
    "Tania Vulcano",
    "Music on",
]

FIELDNAMES = ["query", "mix_title", "mix_url", "part", "position", "timestamp", "artist", "title", "raw"]


def collect_tracklists(queries: list[str], limit: int, strict: bool) -> list[dict]:
    all_tracks = []

    for query in queries:
        print(f"\nSearching MixesDB for '{query}'...")
        results = search(query, limit=limit, strict=strict)
        print(f"Found {len(results)} mix(es) with '{query}' in the title.")

        for r in results:
            try:
                tracks = get_tracklist(r["url"])
            except Exception as e:
                print(f"  Could not fetch tracklist for {r['title']}: {e}")
                continue

            if not tracks:
                continue

            for t in tracks:
                all_tracks.append({"query": query, "mix_title": r["title"], "mix_url": r["url"], **t})

    return all_tracks


def main():
    parser = argparse.ArgumentParser(
        description="Search MixesDB for a list of DJs/queries and fetch every match's tracklist."
    )
    parser.add_argument(
        "queries",
        nargs="*",
        help="One or more search terms, e.g. \"Nick Curly\" \"Barem\". Defaults to a built-in DJ list if omitted.",
    )
    parser.add_argument("--limit", type=int, default=20, help="Max number of matching mixes per query (default: 20)")
    parser.add_argument(
        "--out",
        default="multi_dj_tracklists.csv",
        help="Path to write the combined CSV (default: multi_dj_tracklists.csv)",
    )
    parser.add_argument(
        "--no-filter",
        action="store_true",
        help="Keep MediaWiki's raw relevance results even if they don't literally contain the search word(s)",
    )
    args = parser.parse_args()

    queries = args.queries or DEFAULT_QUERIES

    all_tracks = collect_tracklists(queries, limit=args.limit, strict=not args.no_filter)

    if not all_tracks:
        print("\nNo tracklists found for any query.")
        return

    with open(args.out, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(all_tracks)

    mixes = {(t["query"], t["mix_url"]) for t in all_tracks}
    query_word = "query" if len(queries) == 1 else "queries"
    print(f"\nSaved {len(all_tracks)} tracks across {len(mixes)} mix(es) and {len(queries)} {query_word} to {args.out}")


if __name__ == "__main__":
    main()
