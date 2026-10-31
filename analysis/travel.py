"""How far did a DJ travel between gigs? Great-circle km from each located set
to the next, in date order.

Usage:
    python analysis/travel.py richie_hawtin
    python analysis/travel.py villalobos --from 2004 --to 2008 --legs

Only sets with a full date (YYYY-MM-DD) and a city we have coordinates for are
used, so the totals are a lower bound: real tours have many more gigs (and
flights) than MixesDB has tracklists for, and distances are straight lines.
"""

import argparse
import collections
import math
import re

from common import force_utf8_stdout, load
from locations import locate

# City -> (lat, lon). Covers the cities locations.py finds in the DJ files.
COORDS = {
    "Ibiza": (38.91, 1.43), "Amsterdam": (52.37, 4.90), "Berlin": (52.52, 13.40), "Detroit": (42.33, -83.05),
    "Mannheim": (49.49, 8.47), "Barcelona": (41.39, 2.17), "Ghent": (51.05, 3.72), "Gent": (51.05, 3.72),
    "Tokyo": (35.68, 139.69), "London": (51.51, -0.13), "Miami": (25.76, -80.19), "New York": (40.71, -74.01),
    "Paris": (48.86, 2.35), "Buenos Aires": (-34.60, -58.38), "Kassel": (51.31, 9.48), "Boom": (51.09, 4.37),
    "Indio": (33.72, -116.22), "Dortmund": (51.51, 7.47), "Frankfurt": (50.11, 8.68), "Santiago": (-33.45, -70.67),
    "Munich": (48.14, 11.58), "Manchester": (53.48, -2.24), "Los Angeles": (34.05, -118.24), "Perth": (-31.95, 115.86),
    "Leipzig": (51.34, 12.37), "Johannesburg": (-26.20, 28.05), "Zurich": (47.38, 8.54), "Copenhagen": (55.68, 12.57),
    "Punta Del Este": (-34.96, -54.95), "Cordoba": (-31.42, -64.18), "Chicago": (41.88, -87.63), "Sydney": (-33.87, 151.21),
    "Belgrade": (44.79, 20.45), "Denver": (39.74, -104.99), "Budapest": (47.50, 19.04), "Las Vegas": (36.17, -115.14),
    "Madrid": (40.42, -3.70), "Austin": (30.27, -97.74), "Edinburgh": (55.95, -3.19), "Fraga": (41.52, 0.35),
    "Antwerp": (51.22, 4.40), "Vienna": (48.21, 16.37), "Rosario": (-32.94, -60.65), "Glasgow": (55.86, -4.25),
    "Naples": (40.85, 14.27), "Riccione": (44.00, 12.65), "Liverpool": (53.41, -2.98), "Stuttgart": (48.78, 9.18),
    "Medellin": (6.24, -75.58), "Linz": (48.31, 14.29), "Auckland": (-36.85, 174.76), "Rome": (41.90, 12.50),
    "Montreal": (45.50, -73.57), "Moscow": (55.76, 37.62), "Lyon": (45.76, 4.84), "Vilnius": (54.69, 25.28),
    "Novi Sad": (45.27, 19.83), "Bangkok": (13.76, 100.50), "Kinross": (56.21, -3.42), "Toronto": (43.65, -79.38),
    "Tel-Aviv": (32.09, 34.78), "Tel Aviv": (32.09, 34.78), "Milan": (45.46, 9.19), "Minneapolis": (44.98, -93.27),
    "Wellington": (-41.29, 174.78), "Hamilton": (43.26, -79.87), "Leeds": (53.80, -1.55), "Windsor": (42.31, -83.04),
    "Lokeren": (51.10, 3.99), "Brussels": (50.85, 4.35), "Philadelphia": (39.95, -75.17), "Asheville": (35.60, -82.55),
    "Rotterdam": (51.92, 4.48), "Essen": (51.46, 7.01), "Cologne": (50.94, 6.96), "Hamburg": (53.55, 9.99),
    "Bucharest": (44.43, 26.10), "Lisbon": (38.72, -9.14), "Porto": (41.16, -8.63), "Prague": (50.08, 14.44),
    "Warsaw": (52.23, 21.01), "Krakow": (50.06, 19.94), "Zagreb": (45.81, 15.98), "Athens": (37.98, 23.73),
    "Istanbul": (41.01, 28.98), "Stockholm": (59.33, 18.07), "Oslo": (59.91, 10.75), "Helsinki": (60.17, 24.94),
    "Dublin": (53.35, -6.26), "San Francisco": (37.77, -122.42), "Mexico City": (19.43, -99.13),
    "Playa Del Carmen": (20.63, -87.08), "Sao Paulo": (-23.55, -46.63), "Rio De Janeiro": (-22.91, -43.17),
    "Seoul": (37.57, 126.98), "Shanghai": (31.23, 121.47), "Beijing": (39.90, 116.41), "Singapore": (1.35, 103.82),
    "Melbourne": (-37.81, 144.96), "Valencia": (39.47, -0.38), "Offenbach": (50.10, 8.77), "Riga": (56.95, 24.11),
    "Tbilisi": (41.72, 44.79), "Kiev": (50.45, 30.52), "Kyiv": (50.45, 30.52), "Bogota": (4.71, -74.07), "Lima": (-12.05, -77.04),
    "Montevideo": (-34.90, -56.16), "Vancouver": (49.28, -123.12), "Seattle": (47.61, -122.33), "Boston": (42.36, -71.06),
    "Washington": (38.91, -77.04), "Mamaia": (44.25, 28.62), "Iasi": (47.16, 27.59), "Cluj-Napoca": (46.77, 23.60),
}

# Venue/name hints for titles locations.py can't place (city only).
EXTRA_CITY = {
    "distillery": "Leipzig", "florida 135": "Fraga", "fuse": "Brussels", "cherry moon": "Lokeren", "lokeren": "Lokeren",
    "milano": "Milan", "minneapolis": "Minneapolis", "wellington": "Wellington", "hamilton, ontario": "Hamilton",
    "morley": "Leeds", "maida vale": "London", "10 days off": "Ghent", "windsor": "Windsor",
    "electric factory": "Philadelphia", "moogfest": "Asheville", "sala macumba": "Madrid", "exchange, la": "Los Angeles",
    "mysteryland": "Amsterdam", "dance valley": "Amsterdam", "bloc weekend": "London",
}


def city_of(title: str) -> str | None:
    _, city, _ = locate(title)
    if city in COORDS:
        return city
    low = title.split(" @ ", 1)[-1].lower() if " @ " in title else ""
    for hint, c in EXTRA_CITY.items():
        if hint in low:
            return c
    return None


def km(a: tuple[float, float], b: tuple[float, float]) -> float:
    (lat1, lon1), (lat2, lon2) = (map(math.radians, a)), (map(math.radians, b))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(h))


def main():
    parser = argparse.ArgumentParser(description="Km travelled between a DJ's gigs, in date order.")
    parser.add_argument("dj", help="DJ slug, e.g. richie_hawtin")
    parser.add_argument("--from", dest="start", type=int)
    parser.add_argument("--to", dest="end", type=int)
    parser.add_argument("--legs", action="store_true", help="Print every leg")
    args = parser.parse_args()
    force_utf8_stdout()

    sets, skipped = {}, collections.Counter()
    for r in load(args.dj):
        t = r["mix_title"]
        if r["mix_url"] in sets or r["mix_url"] in skipped:
            continue
        date = re.match(r"(\d{4}-\d{2}-\d{2})", t)
        year = int(t[:4]) if t[:4].isdigit() else None
        if (args.start and (not year or year < args.start)) or (args.end and (not year or year > args.end)):
            continue
        city = city_of(t)
        if not date:
            skipped[r["mix_url"]] = "no full date"
        elif not city:
            skipped[r["mix_url"]] = "no city"
        else:
            sets[r["mix_url"]] = (date.group(1), city, t)

    gigs = sorted(sets.values())
    legs = []
    for prev, cur in zip(gigs, gigs[1:]):
        if prev[1] != cur[1]:
            legs.append((prev, cur, km(COORDS[prev[1]], COORDS[cur[1]])))

    total = sum(d for *_, d in legs)
    print(f"{args.dj}: {len(gigs)} dated, located sets ({len(skipped)} skipped: "
          f"{', '.join(f'{n} {why}' for why, n in collections.Counter(skipped.values()).items())})")
    print(f"{len(legs)} moves between cities, {total:,.0f} km in total "
          f"(≈ {total / 40075:.1f}× around the Earth), average {total / max(len(legs), 1):,.0f} km per move")

    by_year = collections.defaultdict(lambda: [0, 0.0])
    for _, cur, d in legs:
        by_year[cur[0][:4]][0] += 1
        by_year[cur[0][:4]][1] += d
    print("\nyear\tsets\tmoves\tkm")
    sets_per_year = collections.Counter(g[0][:4] for g in gigs)
    for y in sorted(sets_per_year):
        print(f"{y}\t{sets_per_year[y]}\t{by_year[y][0]}\t{by_year[y][1]:,.0f}")

    print("\nlongest moves:")
    for prev, cur, d in sorted(legs, key=lambda l: -l[2])[:10]:
        print(f"  {d:,.0f} km\t{prev[0]} {prev[1]} -> {cur[0]} {cur[1]}")
    cities = collections.Counter(g[1] for g in gigs)
    print("\nmost visited:", " | ".join(f"{c} {n}" for c, n in cities.most_common(10)))
    if args.legs:
        print("\nall legs:")
        for prev, cur, d in legs:
            print(f"  {prev[0]} {prev[1]} -> {cur[0]} {cur[1]}\t{d:,.0f} km")


if __name__ == "__main__":
    main()
