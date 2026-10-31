"""Per-year stats across DJs: mixes, tracks, identification rate, shared tracks,
and the top tracks/artists of each year (by number of DJs, self-plays excluded).

Usage:
    python analysis/year_stats.py --from 2004
    python analysis/year_stats.py --from 2004 --to 2008 --top 5
"""

import argparse
import collections

from common import (add_year_args, force_utf8_stdout, identified, is_self_play, key, load_djs,
                    shared_mixes, split_artists, track_key, track_name, year_of)


def main():
    parser = argparse.ArgumentParser(description="Per-year track/artist stats across DJs.")
    add_year_args(parser)
    parser.add_argument("--top", type=int, default=3, help="Top tracks/artists per year (default: 3)")
    args = parser.parse_args()
    force_utf8_stdout()

    rows = load_djs(args.djs, args.start, args.end)
    shared = shared_mixes(rows)
    mixes, n_rows, n_ident = collections.defaultdict(set), collections.Counter(), collections.Counter()
    djs_in_year = collections.defaultdict(set)
    tracks = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(set)))
    artists = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(set)))
    names = {}

    for d, rs in rows.items():
        for r in rs:
            y = year_of(r)
            if y is None or r["mix_url"] in shared:
                continue
            mixes[y].add(r["mix_url"])
            n_rows[y] += 1
            djs_in_year[y].add(d)
            if not identified(r):
                continue
            n_ident[y] += 1
            if is_self_play(d, r):
                continue
            tracks[y][track_key(r)][d].add(r["mix_url"])
            names.setdefault(track_key(r), track_name(r))
            for a in split_artists(r["artist"]):
                artists[y][key(a)][d].add(r["mix_url"])
                names.setdefault("artist:" + key(a), a)

    def top(m, prefix=""):
        best = sorted(m.items(), key=lambda kv: (-len(kv[1]), -sum(len(s) for s in kv[1].values())))[: args.top]
        return " | ".join(f"{names[prefix + k]} ({len(v)} DJs/{sum(len(s) for s in v.values())} mixes)" for k, v in best)

    print("year\tmixes\ttracks\tDJs\t%identified\tdistinct_tracks\tshared_tracks\tdistinct_artists")
    for y in sorted(mixes):
        shared_tracks = sum(len(v) >= 2 for v in tracks[y].values())
        print(f"{y}\t{len(mixes[y])}\t{n_rows[y]}\t{len(djs_in_year[y])}\t{100 * n_ident[y] / n_rows[y]:.0f}"
              f"\t{len(tracks[y])}\t{shared_tracks}\t{len(artists[y])}")
        print(f"  tracks:  {top(tracks[y])}")
        print(f"  artists: {top(artists[y], 'artist:')}")


if __name__ == "__main__":
    main()
