"""Shared loading and normalisation helpers for the analysis scripts.

Every script reads the CSVs the search workflow commits to data/
(columns: query, mix_title, mix_url, part, position, timestamp, artist, title,
raw). Track/artist matching is deliberately simple: names are compared after
lowercasing and dropping every non-word character, so "Lemon 8 - Model 8" and
"Lemon8 - Model8" count as the same track, but aliases and typos do not.
"""

import collections
import csv
import re
import sys
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# The DJ files analysed by default: data/<slug>_tracklists.csv.
DJS = [
    "adiel", "ben_klock", "dvs1", "ellen_allien", "fadi_mohem", "gaiser", "guido_schneider",
    "jakojako", "len_faki", "loco_dice", "luciano", "luke_slater", "magda", "marc_houle",
    "marcel_dettmann", "marco_carola", "margaret_dygas", "michael_mayer", "nick_curly",
    "onur_ozer", "paco_osuna", "pan_pot", "paul_kalkbrenner", "petre_inspirescu", "raresh",
    "ray_okpara", "rhadoo", "richie_hawtin", "robert_hood", "sonja_moonear", "stephan_bodzin",
    "steve_bug", "troy_pierce", "villalobos", "zip",
]

# A DJ's own names/aliases (as key()s), used to leave out "self-plays" where a
# DJ plays their own record, which says little about what the scene played.
OWN = {
    "marco_carola": {"marcocarola"},
    "richie_hawtin": {"richiehawtin", "plastikman", "fuse"},
    "luciano": {"luciano", "luciennluciano"},
    "villalobos": {"ricardovillalobos"},
    "nick_curly": {"nickcurly"},
    "ray_okpara": {"rayokpara"},
    "magda": {"magda"},
    "troy_pierce": {"troypierce", "loverboy"},
    "loco_dice": {"locodice"},
    "guido_schneider": {"guidoschneider"},
    "onur_ozer": {"onurozer", "onurözer"},
    "pan_pot": {"panpot"},
    "marcel_dettmann": {"marceldettmann"},
    "ben_klock": {"benklock"},
    "robert_hood": {"roberthood", "floorplan"},
    "luke_slater": {"lukeslater", "planetaryassaultsystems", "lbdubcorp"},
    "len_faki": {"lenfaki"},
    "raresh": {"raresh"},
    "dvs1": {"dvs1"},
    "adiel": {"adiel"},
    "jakojako": {"jakojako"},
    "fadi_mohem": {"fadimohem"},
    "marc_houle": {"marchoule"},
    "gaiser": {"gaiser"},
    "rhadoo": {"rhadoo"},
    "petre_inspirescu": {"petreinspirescu", "pedro"},
    "zip": {"zip", "dimbiman", "visionquest"},
    "sonja_moonear": {"sonjamoonear"},
    "margaret_dygas": {"margaretdygas"},
    "steve_bug": {"stevebug", "dogeatdog", "soulcity"},
    "michael_mayer": {"michaelmayer"},
    "paul_kalkbrenner": {"paulkalkbrenner"},
    "ellen_allien": {"ellenallien"},
    "stephan_bodzin": {"stephanbodzin"},
    "paco_osuna": {"pacoosuna"},
}

_PLACEHOLDERS = {"", "id", "unknown", "?", "va"}
_ARTIST_SPLIT_RE = re.compile(r"\s+(?:&|vs\.?|feat\.?|ft\.?|pres\.?)\s+|,\s*", re.IGNORECASE)
_TRAILING_LABEL_RE = re.compile(r"\s*\[[^\]]*\]?\s*$")


def force_utf8_stdout():
    # Same best-effort as the CLI scripts: keep accented names printable on Windows.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass


def csv_path(slug: str) -> Path:
    return DATA_DIR / f"{slug}_tracklists.csv"


def all_slugs() -> list[str]:
    return sorted(p.name[: -len("_tracklists.csv")] for p in DATA_DIR.glob("*_tracklists.csv"))


def load(slug: str) -> list[dict]:
    with open(csv_path(slug), newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def year_of(row: dict) -> int | None:
    y = row["mix_title"][:4]
    return int(y) if y.isdigit() else None


def in_years(row: dict, start: int | None, end: int | None) -> bool:
    if start is None and end is None:
        return True
    y = year_of(row)
    return y is not None and (start is None or y >= start) and (end is None or y <= end)


def load_djs(djs: list[str], start: int | None = None, end: int | None = None) -> dict[str, list[dict]]:
    return {d: [r for r in load(d) if in_years(r, start, end)] for d in djs}


def shared_mixes(rows: dict[str, list[dict]]) -> set[str]:
    """Mix URLs present in more than one DJ's file (b2b sets etc.)."""
    owners = collections.defaultdict(set)
    for d, rs in rows.items():
        for r in rs:
            owners[r["mix_url"]].add(d)
    return {u for u, o in owners.items() if len(o) > 1}


def key(s: str) -> str:
    return re.sub(r"\W", "", s.lower())


def clean(s: str) -> str:
    """Strip a trailing [Label - Cat#] and leading '+' (layered-track marker)."""
    return _TRAILING_LABEL_RE.sub("", s).strip(" +")


def identified(row: dict) -> bool:
    a, t = clean(row["artist"]), clean(row["title"])
    return a.strip(" ?").lower() not in _PLACEHOLDERS and t.strip(" ?").lower() not in _PLACEHOLDERS


def split_artists(artist: str) -> list[str]:
    """'A & B feat. C' -> ['A', 'B', 'C'] so collaborations credit everyone."""
    a = re.sub(r"\[[^\]]*\]?", "", artist).strip(" ?+")
    parts = (p.strip() for p in _ARTIST_SPLIT_RE.split(a))
    return [p for p in parts if p and p.lower() not in _PLACEHOLDERS]


def track_key(row: dict) -> str:
    return key(clean(row["artist"]) + clean(row["title"]))


def track_name(row: dict) -> str:
    return f"{clean(row['artist'])} – {clean(row['title'])}"


_REMIX_CREDIT_RE = re.compile(r"\(([^)]*?)\s*(?:remix|edit|rework|re-edit|mix|dub|version)\)", re.IGNORECASE)


def is_self_play(dj: str, row: dict) -> bool:
    """True if the DJ is a credited artist or the remixer ("Track (DJ Remix)")."""
    own = OWN.get(dj, set())
    if any(key(a) in own for a in split_artists(row["artist"])):
        return True
    return any(key(r) in own for r in _REMIX_CREDIT_RE.findall(row["title"]))


def add_year_args(parser):
    parser.add_argument("--from", dest="start", type=int, help="First mix year to include")
    parser.add_argument("--to", dest="end", type=int, help="Last mix year to include")
    parser.add_argument("--djs", nargs="+", default=DJS, help="DJ slugs to analyse (default: the 35 DJ files)")
