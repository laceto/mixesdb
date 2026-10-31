"""Per-DJ stats plus the tracks/artists shared across DJs.

Usage:
    python analysis/dj_stats.py
    python analysis/dj_stats.py --from 2004 --to 2008
    python analysis/dj_stats.py --djs richie_hawtin villalobos luciano --top 30

Mixes appearing in several DJs' files (b2b sets) are left out of the per-DJ
and cross-DJ counts, and so are self-plays (a DJ playing their own record), so
the rankings show what each DJ took from others.
"""

import argparse
import collections

from common import (add_year_args, force_utf8_stdout, identified, is_self_play, load_djs,
                    shared_mixes, split_artists, track_key, track_name, key)


def main():
    parser = argparse.ArgumentParser(description="Per-DJ and cross-DJ track/artist stats.")
    add_year_args(parser)
    parser.add_argument("--top", type=int, default=15, help="Rows per ranking (default: 15)")
    args = parser.parse_args()
    force_utf8_stdout()

    rows = load_djs(args.djs, args.start, args.end)
    shared = shared_mixes(rows)
    tracks = collections.defaultdict(lambda: collections.defaultdict(set))  # track -> dj -> mixes
    artists = collections.defaultdict(lambda: collections.defaultdict(set))
    names = {}

    print("DJ\tmixes\ttracks\tper_mix\t%identified\tdistinct_tracks\tdistinct_artists\t%own")
    per_dj = []
    for d, rs in rows.items():
        mixes = {r["mix_url"] for r in rs}
        solo = [r for r in rs if r["mix_url"] not in shared]
        ident = [r for r in solo if identified(r)]
        own = sum(is_self_play(d, r) for r in ident)
        dj_tracks = {track_key(r) for r in ident}
        dj_artists = {key(a) for r in ident for a in split_artists(r["artist"])}
        for r in ident:
            if is_self_play(d, r):
                continue
            k = track_key(r)
            tracks[k][d].add(r["mix_url"])
            names.setdefault(k, track_name(r))
            for a in split_artists(r["artist"]):
                artists[key(a)][d].add(r["mix_url"])
                names.setdefault("artist:" + key(a), a)
        per_dj.append((d, len(mixes), len(rs), len(rs) / max(len(mixes), 1),
                       100 * len(ident) / max(len(solo), 1), len(dj_tracks), len(dj_artists),
                       100 * own / max(len(ident), 1)))
    for p in sorted(per_dj, key=lambda p: -p[1]):
        print(f"{p[0]}\t{p[1]}\t{p[2]}\t{p[3]:.0f}\t{p[4]:.0f}\t{p[5]}\t{p[6]}\t{p[7]:.0f}")

    n_mixes = lambda v: sum(len(s) for s in v.values())
    print(f"\nTOTAL rows {sum(len(r) for r in rows.values())} | mixes {len({r['mix_url'] for rs in rows.values() for r in rs})}"
          f" | shared mixes {len(shared)} | distinct tracks {len(tracks)} | distinct artists {len(artists)}")
    print(f"tracks by >=2 DJs {sum(len(v) >= 2 for v in tracks.values())} | >=5 DJs {sum(len(v) >= 5 for v in tracks.values())}"
          f" | in one mix only {sum(n_mixes(v) == 1 for v in tracks.values())}")
    print(f"artists by >=2 DJs {sum(len(v) >= 2 for v in artists.values())} | >=10 DJs {sum(len(v) >= 10 for v in artists.values())}")

    def ranking(title, items, label, sort_key):
        print(f"\n{title}\n#DJs\t#mixes\t{label}\tby")
        for k, v in sorted(items.items(), key=sort_key)[: args.top]:
            by = ", ".join(f"{d} {len(s)}" for d, s in sorted(v.items(), key=lambda i: -len(i[1]))[:5])
            print(f"{len(v)}\t{n_mixes(v)}\t{names[k] if label == 'track' else names['artist:' + k]}\t{by}")

    ranking("TOP TRACKS by number of DJs", tracks, "track", lambda kv: (-len(kv[1]), -n_mixes(kv[1])))
    ranking("TOP TRACKS by number of mixes", tracks, "track", lambda kv: (-n_mixes(kv[1]), -len(kv[1])))
    ranking("TOP ARTISTS by number of DJs", artists, "artist", lambda kv: (-len(kv[1]), -n_mixes(kv[1])))
    ranking("TOP ARTISTS by number of mixes", artists, "artist", lambda kv: (-n_mixes(kv[1]), -len(kv[1])))


if __name__ == "__main__":
    main()
