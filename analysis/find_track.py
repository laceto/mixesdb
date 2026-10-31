"""Find every set (in any data/ CSV) whose tracklist line matches a pattern.

Usage:
    python analysis/find_track.py "brothers of the underground"
    python analysis/find_track.py "lemos.*blow it" --djs-only

The pattern is a case-insensitive regular expression matched against the raw
tracklist line ("Artist - Title [Label]").
"""

import argparse
import re

from common import DJS, all_slugs, force_utf8_stdout, load


def main():
    parser = argparse.ArgumentParser(description="Find sets that played a track.")
    parser.add_argument("pattern", help="Case-insensitive regex matched against each raw tracklist line")
    parser.add_argument("--djs-only", action="store_true", help="Search only the DJ files, not venue/event searches")
    args = parser.parse_args()
    force_utf8_stdout()

    pattern = re.compile(args.pattern, re.IGNORECASE)
    seen = {}
    for slug in (DJS if args.djs_only else all_slugs()):
        for r in load(slug):
            if pattern.search(r.get("raw", "")):
                seen.setdefault((r["mix_url"], r["part"], r["position"]), (slug, r))
    for (url, _, _), (slug, r) in sorted(seen.items(), key=lambda kv: kv[1][1]["mix_title"]):
        where = " ".join(v for v in (r["part"], f"#{r['position']}", r["timestamp"]) if v)
        print(f"{r['mix_title']} | {where} | {r['raw']} | {url} (from {slug})")
    print(f"\n{len(seen)} plays in {len({k[0] for k in seen})} sets")


if __name__ == "__main__":
    main()
