"""CLI: search MixesDB and list matching mix page URLs.

Thin wrapper over the mixesdb package's search().

Usage:
    python mixesdb_scraper.py hawtin
    python mixesdb_scraper.py "richie hawtin" --limit 50 --out results.csv
    python mixesdb_scraper.py "richie hawtin" --limit 50 --out results.csv --no-filter
"""

import argparse
import csv
import sys

from mixesdb.search import search

# Windows consoles often use a legacy codepage (e.g. CP850) that can't encode
# accented characters common in mix titles (e.g. "Sven Väth"), which raises
# UnicodeEncodeError on print(). Force UTF-8 with a safe fallback. Not all
# stdout streams support reconfigure() (e.g. Jupyter's), so this is best-effort.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass


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
