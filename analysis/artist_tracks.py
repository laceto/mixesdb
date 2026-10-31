"""List every track by the given artist(s) across the DJ files: mixes, DJs, years.

Usage:
    python analysis/artist_tracks.py "Minilogue"
    python analysis/artist_tracks.py "Santos" "Chris Carrier" --from 2004 --to 2010
"""

import argparse
import collections

from common import add_year_args, force_utf8_stdout, key, load_djs, split_artists, track_key, track_name, year_of


def main():
    parser = argparse.ArgumentParser(description="Every track by the given artist(s) and who played it.")
    parser.add_argument("artists", nargs="+", help="Artist name(s), matched against each credited artist")
    add_year_args(parser)
    args = parser.parse_args()
    force_utf8_stdout()

    rows = load_djs(args.djs, args.start, args.end)
    for target in args.artists:
        found = collections.defaultdict(lambda: {"mixes": set(), "djs": set(), "years": set()})
        names = {}
        for d, rs in rows.items():
            for r in rs:
                if key(target) not in {key(a) for a in split_artists(r["artist"])}:
                    continue
                e = found[track_key(r)]
                e["mixes"].add(r["mix_url"])
                e["djs"].add(d)
                if year_of(r):
                    e["years"].add(year_of(r))
                names.setdefault(track_key(r), track_name(r))
        print(f"== {target}: {len(found)} distinct tracks")
        for k, e in sorted(found.items(), key=lambda kv: (-len(kv[1]["mixes"]), names[kv[0]])):
            ys = sorted(e["years"])
            years = "" if not ys else str(ys[0]) if len(ys) == 1 else f"{ys[0]}–{ys[-1]}"
            print(f"{len(e['mixes'])}\t{names[k]}\t{'/'.join(sorted(e['djs']))}\t{years}")


if __name__ == "__main__":
    main()
