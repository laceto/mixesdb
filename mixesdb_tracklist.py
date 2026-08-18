"""CLI: scrape the tracklist from a single MixesDB mix page.

Thin wrapper over the mixesdb package's get_tracklist().

Usage:
    python mixesdb_tracklist.py "https://www.mixesdb.com/w/2006-08-16_-_Richie_Hawtin_@_Cocorico,_Riccione"
    python mixesdb_tracklist.py "<url>" --out tracklist.csv
"""

import argparse
import csv
import sys

from mixesdb.tracklist import get_tracklist

# Windows consoles often use a legacy codepage (e.g. CP850) that can't encode
# accented characters common in mix titles (e.g. "Sven Väth"), which raises
# UnicodeEncodeError on print(). Force UTF-8 with a safe fallback. Not all
# stdout streams support reconfigure() (e.g. Jupyter's), so this is best-effort.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass


def main():
    parser = argparse.ArgumentParser(description="Scrape the tracklist from a MixesDB mix page.")
    parser.add_argument("url", help="Full MixesDB mix page URL")
    parser.add_argument("--out", help="Optional path to write results as CSV")
    args = parser.parse_args()

    tracks = get_tracklist(args.url)

    if not tracks:
        print("No tracklist found on this page.")
        return

    current_part = None
    for t in tracks:
        if t["part"] != current_part:
            current_part = t["part"]
            if current_part:
                print(f"\n-- {current_part} --")
        ts = f"[{t['timestamp']}] " if t["timestamp"] else ""
        if t["artist"]:
            print(f"{t['position']:>3}. {ts}{t['artist']} - {t['title']}")
        else:
            print(f"{t['position']:>3}. {ts}{t['raw']}")

    if args.out:
        with open(args.out, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=["part", "position", "timestamp", "artist", "title", "raw"])
            writer.writeheader()
            writer.writerows(tracks)
        print(f"\nSaved {len(tracks)} tracks to {args.out}")


if __name__ == "__main__":
    main()
