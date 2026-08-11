"""Scrape the tracklist from a single MixesDB mix page.

Fetches the page's raw wikitext (via action=raw) and parses the
"== Tracklist ==" section into structured track entries. Handles pages
split into parts/sets (";Part 1", ";Part 2", ...) and timestamp-prefixed
entries ("# [12:34] Artist - Title").

Usage:
    python mixesdb_tracklist.py "https://www.mixesdb.com/w/2006-08-16_-_Richie_Hawtin_@_Cocorico,_Riccione"
    python mixesdb_tracklist.py "<url>" --out tracklist.csv
"""

import argparse
import csv
import re
import sys
import urllib.parse
import urllib.request

USER_AGENT = "Mozilla/5.0 (compatible; mixesdb-scraper/1.0)"

TIMESTAMP_RE = re.compile(r"^\[([0-9?:]+)\]\s*")
WIKILINK_RE = re.compile(r"\[\[(?:[^\]|]*\|)?([^\]]+)\]\]")
TEMPLATE_RE = re.compile(r"\{\{[^}]*\}\}")
BOLD_ITALIC_RE = re.compile(r"'{2,3}")

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except AttributeError:
    pass


def url_to_title(url: str) -> str:
    path = urllib.parse.urlparse(url).path
    title = path.split("/w/", 1)[-1]
    return urllib.parse.unquote(title)


def fetch_raw_wikitext(title: str) -> str:
    params = {"title": title, "action": "raw"}
    api_url = f"https://www.mixesdb.com/w/index.php?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(api_url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8")


def clean_wikitext(text: str) -> str:
    text = WIKILINK_RE.sub(r"\1", text)
    text = TEMPLATE_RE.sub("", text)
    text = BOLD_ITALIC_RE.sub("", text)
    return text.strip()


def extract_tracklist_section(wikitext: str) -> str:
    match = re.search(r"^==\s*Tracklist\s*==\s*$", wikitext, re.MULTILINE | re.IGNORECASE)
    if not match:
        return ""
    start = match.end()
    next_section = re.search(r"^==[^=].*==\s*$", wikitext[start:], re.MULTILINE)
    end = start + next_section.start() if next_section else len(wikitext)
    return wikitext[start:end]


def parse_tracklist(wikitext: str) -> list[dict]:
    section = extract_tracklist_section(wikitext)
    if not section.strip():
        return []

    tracks = []
    current_part = None
    index_in_part = 0

    for line in section.splitlines():
        line = line.strip()
        if not line:
            continue

        if line.startswith(";"):
            current_part = clean_wikitext(line.lstrip(";").strip())
            index_in_part = 0
            continue

        if line.startswith("#"):
            content = line.lstrip("#").strip()
            index_in_part += 1

            ts_match = TIMESTAMP_RE.match(content)
            timestamp = ts_match.group(1) if ts_match else ""
            remainder = content[ts_match.end():].strip() if ts_match else content
            remainder = clean_wikitext(remainder)

            artist, title = "", remainder
            for sep in (" - ", " – ", " — "):
                if sep in remainder:
                    artist, title = remainder.split(sep, 1)
                    artist, title = artist.strip(), title.strip()
                    break

            tracks.append(
                {
                    "part": current_part or "",
                    "position": index_in_part,
                    "timestamp": timestamp,
                    "artist": artist,
                    "title": title,
                    "raw": remainder,
                }
            )

    return tracks


def get_tracklist(url: str) -> list[dict]:
    title = url_to_title(url)
    wikitext = fetch_raw_wikitext(title)
    return parse_tracklist(wikitext)


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
