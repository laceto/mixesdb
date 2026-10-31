"""Top tracks and artists for each DJ (by number of mixes), self-plays included.

Usage:
    python analysis/dj_top.py --djs marco_carola richie_hawtin
    python analysis/dj_top.py --from 2005 --to 2010 --top 8
"""

import argparse
import collections

from common import (add_year_args, force_utf8_stdout, identified, key, load_djs, shared_mixes,
                    split_artists, track_key, track_name)


def main():
    parser = argparse.ArgumentParser(description="Top tracks and artists per DJ.")
    add_year_args(parser)
    parser.add_argument("--top", type=int, default=6, help="Entries per DJ (default: 6)")
    args = parser.parse_args()
    force_utf8_stdout()

    rows = load_djs(args.djs, args.start, args.end)
    shared = shared_mixes(rows)
    for d, rs in rows.items():
        solo = [r for r in rs if r["mix_url"] not in shared and identified(r)]
        tracks, artists, names = collections.defaultdict(set), collections.defaultdict(set), {}
        for r in solo:
            tracks[track_key(r)].add(r["mix_url"])
            names[track_key(r)] = track_name(r)
            for a in split_artists(r["artist"]):
                artists[key(a)].add(r["mix_url"])
                names.setdefault("artist:" + key(a), a)
        n = len({r["mix_url"] for r in rs if r["mix_url"] not in shared})
        print(f"== {d} ({n} mixes)")
        print("  tracks: ", " | ".join(f"{names[k]} {len(v)}" for k, v in sorted(tracks.items(), key=lambda kv: -len(kv[1]))[: args.top]))
        print("  artists:", " | ".join(f"{names['artist:' + k]} {len(v)}" for k, v in sorted(artists.items(), key=lambda kv: -len(kv[1]))[: args.top]))


if __name__ == "__main__":
    main()
