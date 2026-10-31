"""Where were the sets played? Parses the location out of every mix title in data/.

Usage:
    python analysis/locations.py
    python analysis/locations.py --from 2004 --to 2008 --top 30

MixesDB titles look like "2008-04-05 - DJ @ Venue, City, Country (Extra)".
The venue is the first part after " @ "; city and country are matched against
the lookup tables below (plus festival/venue names that imply a city). Sets
without " @ " (radio shows, podcasts, promo mixes) have no location. Each mix is
counted once even if it appears in several CSVs.
"""

import argparse
import collections
import re

from common import all_slugs, force_utf8_stdout, load

CITY_COUNTRY = {
'berlin':'Germany','mannheim':'Germany','munich':'Germany','münchen':'Germany','frankfurt':'Germany','offenbach':'Germany','cologne':'Germany','köln':'Germany','hamburg':'Germany','leipzig':'Germany','dortmund':'Germany','stuttgart':'Germany','düsseldorf':'Germany','essen':'Germany','dresden':'Germany','karlsruhe':'Germany','bochum':'Germany','nuremberg':'Germany','hannover':'Germany','weimar':'Germany','mainz':'Germany','bremen':'Germany','freiburg':'Germany','heidelberg':'Germany','kassel':'Germany','gräfenhainichen':'Germany','ferropolis':'Germany',
'london':'UK','manchester':'UK','glasgow':'UK','edinburgh':'UK','leeds':'UK','liverpool':'UK','birmingham':'UK','bristol':'UK','brighton':'UK','sheffield':'UK','newcastle':'UK','nottingham':'UK','belfast':'UK','cardiff':'UK','kinross':'UK','bournemouth':'UK',
'ibiza':'Spain','barcelona':'Spain','madrid':'Spain','valencia':'Spain','bilbao':'Spain','malaga':'Spain','tenerife':'Spain','mallorca':'Spain','san sebastian':'Spain','monegros':'Spain',
'amsterdam':'Netherlands','rotterdam':'Netherlands','utrecht':'Netherlands','eindhoven':'Netherlands','the hague':'Netherlands','den haag':'Netherlands','spaarnwoude':'Netherlands','nijmegen':'Netherlands','groningen':'Netherlands','tilburg':'Netherlands','amsterdam dance event':'Netherlands','ade':'Netherlands',
'brussels':'Belgium','antwerp':'Belgium','ghent':'Belgium','gent':'Belgium','liège':'Belgium','leuven':'Belgium','boom':'Belgium','dour':'Belgium',
'paris':'France','lyon':'France','marseille':'France','bordeaux':'France','lille':'France','nice':'France','toulouse':'France',
'rome':'Italy','milan':'Italy','naples':'Italy','napoli':'Italy','turin':'Italy','torino':'Italy','florence':'Italy','bologna':'Italy','riccione':'Italy','rimini':'Italy','verona':'Italy','venice':'Italy','padova':'Italy','bari':'Italy','catania':'Italy','palermo':'Italy','sardinia':'Italy','salerno':'Italy',
'vienna':'Austria','graz':'Austria','linz':'Austria','zurich':'Switzerland','zürich':'Switzerland','geneva':'Switzerland','basel':'Switzerland','bern':'Switzerland','lausanne':'Switzerland',
'bucharest':'Romania','cluj-napoca':'Romania','cluj':'Romania','iasi':'Romania','timisoara':'Romania','brasov':'Romania','sibiu':'Romania','constanta':'Romania',
'prague':'Czech Republic','brno':'Czech Republic','warsaw':'Poland','krakow':'Poland','wroclaw':'Poland','gdansk':'Poland','budapest':'Hungary','belgrade':'Serbia','novi sad':'Serbia','zagreb':'Croatia','split':'Croatia','ljubljana':'Slovenia','sofia':'Bulgaria','athens':'Greece','thessaloniki':'Greece','mykonos':'Greece','istanbul':'Turkey','tel aviv':'Israel','moscow':'Russia','st. petersburg':'Russia','saint petersburg':'Russia','kiev':'Ukraine','kyiv':'Ukraine','tbilisi':'Georgia','riga':'Latvia','tallinn':'Estonia','vilnius':'Lithuania','minsk':'Belarus',
'lisbon':'Portugal','porto':'Portugal','copenhagen':'Denmark','stockholm':'Sweden','gothenburg':'Sweden','malmö':'Sweden','oslo':'Norway','helsinki':'Finland','reykjavik':'Iceland','dublin':'Ireland','cork':'Ireland',
'miami':'USA','new york':'USA','nyc':'USA','brooklyn':'USA','detroit':'USA','chicago':'USA','los angeles':'USA','san francisco':'USA','las vegas':'USA','washington':'USA','boston':'USA','philadelphia':'USA','seattle':'USA','denver':'USA','austin':'USA','houston':'USA','atlanta':'USA','indio':'USA','coachella':'USA','miami beach':'USA','wmc':'USA','mmw':'USA','san diego':'USA','portland':'USA','montreal':'Canada','toronto':'Canada','vancouver':'Canada',
'buenos aires':'Argentina','córdoba':'Argentina','cordoba':'Argentina','rosario':'Argentina','santiago':'Chile','sao paulo':'Brazil','são paulo':'Brazil','rio de janeiro':'Brazil','florianopolis':'Brazil','florianópolis':'Brazil','mexico city':'Mexico','playa del carmen':'Mexico','tulum':'Mexico','bogota':'Colombia','bogotá':'Colombia','medellin':'Colombia','medellín':'Colombia','lima':'Peru','montevideo':'Uruguay','punta del este':'Uruguay','caracas':'Venezuela',
'tokyo':'Japan','osaka':'Japan','seoul':'South Korea','beijing':'China','shanghai':'China','hong kong':'Hong Kong','singapore':'Singapore','bangkok':'Thailand','koh phangan':'Thailand','bali':'Indonesia','manila':'Philippines','mumbai':'India','goa':'India','bangalore':'India','new delhi':'India','dubai':'UAE','abu dhabi':'UAE','beirut':'Lebanon','cairo':'Egypt','tel-aviv':'Israel','cape town':'South Africa','johannesburg':'South Africa','sydney':'Australia','melbourne':'Australia','brisbane':'Australia','perth':'Australia','auckland':'New Zealand','taipei':'Taiwan','reykjavík':'Iceland','reykjavik':'Iceland','bratislava':'Slovakia','luxembourg':'Luxembourg',
}

# Venue/festival names that imply a city when the title gives none.
VENUE_CITY = {'dc10':('Ibiza','Spain'),'dc-10':('Ibiza','Spain'),'sonar':('Barcelona','Spain'),'sónar':('Barcelona','Spain'),'awakenings':('Amsterdam','Netherlands'),
'tomorrowland':('Boom','Belgium'),'mayday':('Dortmund','Germany'),'globus':('Berlin','Germany'),'tresor':('Berlin','Germany'),'berghain':('Berlin','Germany'),
'panorama bar':('Berlin','Germany'),'time warp':('Mannheim','Germany'),'nature one':('Kastellaun','Germany'),'i love techno':('Ghent','Belgium'),
'fusion festival':('Lärz','Germany'),'melt!':('Gräfenhainichen','Germany'),'demf':('Detroit','USA'),'movement':('Detroit','USA'),'mutek':('Montreal','Canada'),
'snagov':('Snagov','Romania'),'amnesia':('Ibiza','Spain'),'pacha, ibiza':('Ibiza','Spain'),'space, ibiza':('Ibiza','Spain'),'privilege':('Ibiza','Spain'),
'watergate':('Berlin','Germany'),'bar25':('Berlin','Germany'),'robert johnson':('Offenbach','Germany'),'cocorico':('Riccione','Italy'),'loveparade':('Berlin','Germany'),
'love parade':('Berlin','Germany'),'the bpm festival':('Playa del Carmen','Mexico'),'warehouse project':('Manchester','UK'),'creamfields':('Daresbury','UK'),
'glastonbury':('Pilton','UK'),'t in the park':('Kinross','UK'),'dance under the blue moon':('Essen','Germany'),'sunwaves':('Mamaia','Romania'),'dekmantel':('Amsterdam','Netherlands'),
'ultra music festival, wmc':('Miami','USA'),'ultra music festival, mmw':('Miami','USA'),'surfcomber':('Miami','USA'),'treehouse, miami':('Miami','USA'),'exit festival':('Novi Sad','Serbia'),'monegros':('Fraga','Spain')}

COUNTRIES = {v.lower() for v in CITY_COUNTRY.values()} | {'germany','uk','united kingdom','england','scotland','wales','spain','netherlands','holland','belgium','france','italy','austria','switzerland','romania','portugal','usa','us','united states','canada','argentina','chile','brazil','mexico','colombia','japan','australia','croatia','serbia','greece','turkey','israel','russia','poland','hungary','czech republic','denmark','sweden','norway','finland','ireland','india','south africa','peru','uruguay','china','thailand','south korea','korea','lebanon','uae','bulgaria','slovenia','slovakia','ukraine','georgia','estonia','latvia','lithuania','iceland','luxembourg','malta','cyprus','montenegro','bosnia','macedonia','albania','morocco','egypt','tunisia','new zealand','singapore','indonesia','philippines','taiwan','hong kong','venezuela','ecuador','costa rica','dominican republic','puerto rico','panama','cuba'}
COUNTRY_ALIASES = {"united kingdom": "UK", "england": "UK", "scotland": "UK", "wales": "UK", "holland": "Netherlands",
                   "us": "USA", "united states": "USA", "korea": "South Korea", "uk": "UK", "usa": "USA", "uae": "UAE"}
CITY_ALIASES = {"wmc": "Miami", "mmw": "Miami", "nyc": "New York", "ade": "Amsterdam"}
CANONICAL_COUNTRY = {c.lower(): c for c in CITY_COUNTRY.values()}


def locate(title: str) -> tuple[str | None, str | None, str | None]:
    """Return (venue, city, country) for a mix title; any may be None."""
    if " @ " not in title:
        return None, None, None
    v = re.sub(r"\([^)]*\)", "", title.split(" @ ", 1)[1]).replace(" - ", ", ")
    parts = [p.strip() for p in v.split(",") if p.strip()]
    if not parts:
        return None, None, None
    city = country = None
    for p in reversed(parts):
        low = p.lower()
        if low in COUNTRIES and not country:
            country = COUNTRY_ALIASES.get(low, p)
            continue
        if low in CITY_COUNTRY:
            city = CITY_ALIASES.get(low, p.title())
            country = country or CITY_COUNTRY[low]
            break
    if not country:
        for name, (c_city, c_country) in VENUE_CITY.items():
            if name in v.lower():
                city, country = city or c_city, c_country
                break
    if not country:
        for p in parts:
            for name, c in CITY_COUNTRY.items():
                if re.search(r"\b" + re.escape(name) + r"\b", p.lower()):
                    country, city = c, city or CITY_ALIASES.get(name, name.title())
                    break
            if country:
                break
    if country:
        country = CANONICAL_COUNTRY.get(country.lower(), country)
    return parts[0], city, country


def main():
    parser = argparse.ArgumentParser(description="Country/city/venue stats from the mix titles in data/.")
    parser.add_argument("--from", dest="start", type=int)
    parser.add_argument("--to", dest="end", type=int)
    parser.add_argument("--top", type=int, default=20)
    args = parser.parse_args()
    force_utf8_stdout()

    titles = {}
    for slug in all_slugs():
        for r in load(slug):
            titles.setdefault(r["mix_url"], r["mix_title"])
    sets = []
    for title in titles.values():
        year = int(title[:4]) if title[:4].isdigit() else None
        if (args.start and (not year or year < args.start)) or (args.end and (not year or year > args.end)):
            continue
        sets.append((title, year, *locate(title)))

    with_venue = sum(" @ " in s[0] for s in sets)
    located = [s for s in sets if s[4]]
    print(f"{len(sets)} sets | with a venue {with_venue} ({100 * with_venue / max(len(sets), 1):.0f}%)"
          f" | country found {len(located)} ({100 * len(located) / max(len(sets), 1):.0f}%)")
    countries = collections.Counter(s[4] for s in located)
    cities = collections.Counter(s[3] for s in sets if s[3])
    venues = collections.Counter(f"{s[2]} ({s[3] or s[4] or '?'})" for s in sets if s[2])
    print(f"{len(countries)} countries, {len(cities)} cities")
    print("countries:", " | ".join(f"{c} {n}" for c, n in countries.most_common(args.top)))
    print("cities:", " | ".join(f"{c} {n}" for c, n in cities.most_common(args.top)))
    print("venues:", " | ".join(f"{v} {n}" for v, n in venues.most_common(args.top)))

    periods = [(1990, 1999), (2000, 2003), (2004, 2008), (2009, 2013), (2014, 2019), (2020, 2029)]
    top = [c for c, _ in countries.most_common(10)]
    print("\nsets per period", *top, sep="\t")
    for lo, hi in periods:
        c = collections.Counter(s[4] for s in located if s[1] and lo <= s[1] <= hi)
        if sum(c.values()):
            print(f"{lo}-{hi}", *[c[t] for t in top], sep="\t")


if __name__ == "__main__":
    main()
