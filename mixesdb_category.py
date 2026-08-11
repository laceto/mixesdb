"""List all mix pages under a MixesDB category.

Uses the MediaWiki action API (list=categorymembers) to enumerate every
page in a category, e.g. https://www.mixesdb.com/w/Category:Richie_Hawtin

Usage:
    python mixesdb_category.py "https://www.mixesdb.com/w/Category:Richie_Hawtin"
    python mixesdb_category.py "Category:Richie Hawtin" --out category.csv
"""

import argparse
import csv
import sys
import time
import urllib.parse
import urllib.request
import json

API_URL = "https://www.mixesdb.com/w/api.php"
BASE_PAGE_URL = "https://www.mixesdb.com/w/"
USER_AGENT = "Mozilla/5.0 (compatible; mixesdb-scraper/1.0)"
MAX_PER_REQUEST = 500

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass


def title_to_url(title: str) -> str:
    return BASE_PAGE_URL + urllib.parse.quote(title.replace(" ", "_"), safe="/:@,()!'&+")


def url_to_category_title(value: str) -> str:
    """Accept either a full category URL or a bare 'Category:Name' string."""
    if value.startswith("http"):
        path = urllib.parse.urlparse(value).path
        title = path.split("/w/", 1)[-1]
        return urllib.parse.unquote(title).replace("_", " ")
    return value


def list_category_members(category: str, limit: int | None = None) -> list[dict]:
    """Return [{title, url, namespace}] for every page in the category (subcategories excluded)."""
    cmtitle = category if category.startswith("Category:") else f"Category:{category}"
    members = []
    cmcontinue = None

    while True:
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": cmtitle,
            "cmlimit": MAX_PER_REQUEST,
            "cmtype": "page",
            "format": "json",
        }
        if cmcontinue:
            params["cmcontinue"] = cmcontinue

        url = f"{API_URL}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        for m in data.get("query", {}).get("categorymembers", []):
            members.append({"title": m["title"], "url": title_to_url(m["title"])})
            if limit and len(members) >= limit:
                return members

        cmcontinue = data.get("continue", {}).get("cmcontinue")
        if not cmcontinue:
            break
        time.sleep(0.2)

    return members


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
