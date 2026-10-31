"""Stats for a venue/event search file: sets per year, DJs, top tracks.

Usage:
    python analysis/venue_stats.py tresor
    python analysis/venue_stats.py fabric --title-regex "\\bfabric\\b" --from 2004 --to 2008

The first argument is the CSV slug (data/<slug>_tracklists.csv). --title-regex
drops sets whose title doesn't match, for keywords that also hit unrelated
titles (e.g. "Fabriclive" CDs in the fabric search).
"""

import argparse
import collections
import re

from common import force_utf8_stdout, in_years, identified, key, load, split_artists, track_key, track_name, year_of

LABEL_RE = re.compile(r"\[([^\]\-]+?)(?:\s*-\s*[^\]]*)?\]")


def dj_names(title: str) -> list[str]:
    name = re.sub(r"^[\dX\-]+ - ", "", title).split(" @ ")[0]
    parts = (re.sub(r"\s*\((Live|Live PA|DJ Set|Live AV)[^)]*\)", "", p, flags=re.IGNORECASE).strip()
             for p in re.split(r",\s*|\s+(?:&|b2b|b3b|vs\.?)\s+", name, flags=re.IGNORECASE))
    return [p for p in parts if p and p not in ("VA", "Various")]


def main():
    parser = argparse.ArgumentParser(description="Stats for a venue/event search CSV.")
    parser.add_argument("slug", help="CSV slug, e.g. tresor, circoloco, fabric")
    parser.add_argument("--title-regex", help="Keep only sets whose title matches this regex")
    parser.add_argument("--from", dest="start", type=int)
    parser.add_argument("--to", dest="end", type=int)
    parser.add_argument("--top", type=int, default=20)
    args = parser.parse_args()
    force_utf8_stdout()

    rows = [r for r in load(args.slug) if in_years(r, args.start, args.end)]
    if args.title_regex:
        rows = [r for r in rows if re.search(args.title_regex, r["mix_title"], re.IGNORECASE)]
    sets = {r["mix_url"]: r["mix_title"] for r in rows}
    years = collections.Counter(year_of({"mix_title": t}) for t in sets.values())
    djs = collections.Counter(n for t in sets.values() for n in dj_names(t))
    tracks, artists, labels, names = collections.defaultdict(set), collections.defaultdict(set), collections.Counter(), {}
    for r in rows:
        found = LABEL_RE.findall(r["raw"])
        if found:
            labels[found[-1].strip()] += 1
        if not identified(r):
            continue
        tracks[track_key(r)].add(r["mix_url"])
        names[track_key(r)] = track_name(r)
        for a in split_artists(r["artist"]):
            artists[key(a)].add(r["mix_url"])
            names.setdefault("artist:" + key(a), a)

    ident = sum(identified(r) for r in rows)
    print(f"{args.slug}: {len(sets)} sets, {len(rows)} tracks, {len(djs)} DJs, "
          f"{100 * ident / max(len(rows), 1):.0f}% identified, {len(tracks)} distinct tracks, {len(artists)} artists")
    print("sets per year:", " ".join(f"{y}:{n}" for y, n in sorted((y, n) for y, n in years.items() if y)))
    print("top DJs:", " | ".join(f"{d} {n}" for d, n in djs.most_common(args.top)))
    print("top tracks:", " | ".join(f"{names[k]} {len(v)}" for k, v in sorted(tracks.items(), key=lambda kv: -len(kv[1]))[: args.top]))
    print("top artists:", " | ".join(f"{names['artist:' + k]} {len(v)}" for k, v in sorted(artists.items(), key=lambda kv: -len(kv[1]))[: args.top]))
    print("top labels (plays):", " | ".join(f"{l} {n}" for l, n in labels.most_common(args.top)))


if __name__ == "__main__":
    main()
