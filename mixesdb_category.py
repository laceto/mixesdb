"""CLI: list all mix pages under a MixesDB category.

Thin wrapper over the mixesdb package's list_category_members().

Usage:
    python mixesdb_category.py "https://www.mixesdb.com/w/Category:Richie_Hawtin"
    python mixesdb_category.py "Category:Richie Hawtin" --out category.csv
"""

import argparse
import csv
import sys

from mixesdb.category import list_category_members, url_to_category_title

# Windows consoles often use a legacy codepage (e.g. CP850) that can't encode
# accented characters common in mix titles (e.g. "Sven Väth"), which raises
# UnicodeEncodeError on print(). Force UTF-8 with a safe fallback. Not all
# stdout streams support reconfigure() (e.g. Jupyter's), so this is best-effort.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass


def main():
    parser = argparse.ArgumentParser(description="List all mix pages in a MixesDB category.")
    parser.add_argument("category", help="Category URL or name, e.g. 'https://www.mixesdb.com/w/Category:Richie_Hawtin'")
    parser.add_argument("--limit", type=int, default=None, help="Max number of pages to list (default: all)")
    parser.add_argument("--out", help="Optional path to write results as CSV")
    args = parser.parse_args()

    cat_title = url_to_category_title(args.category)
    members = list_category_members(cat_title, limit=args.limit)

    if not members:
        print(f"No pages found in '{cat_title}'.")
        return

    for i, m in enumerate(members, 1):
        print(f"{i}. {m['title']}\n   {m['url']}")

    if args.out:
        with open(args.out, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=["title", "url"])
            writer.writeheader()
            writer.writerows(members)
        print(f"\nSaved {len(members)} pages to {args.out}")


if __name__ == "__main__":
    main()
