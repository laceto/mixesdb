"""Full-text search against MixesDB.

Uses the MediaWiki action API (/w/api.php) rather than parsing the search
results page HTML, since that page renders its results client-side via
JavaScript and has nothing to parse server-side.
"""

import json
import re
import time
import urllib.parse
import urllib.request

from ._shared import API_URL, USER_AGENT, title_to_url

MAX_PER_REQUEST = 50  # MediaWiki API srlimit cap for anonymous users


def matches_query(title: str, query: str) -> bool:
    """True only if every word of the query literally appears in the page title.

    MediaWiki's search is relevance-based, not a strict substring match: it can
    return pages that only mention the query words somewhere in the page body
    (e.g. as a track credit in a tracklist) rather than in the title/lineup.
    Restricting to the title keeps only mixes where the query is actually part
    of the mix's own name (e.g. the performing artist).
    """
    title_lower = title.lower()
    return all(word in title_lower for word in query.lower().split())


def strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).replace("&nbsp;", " ").strip()


def search(query: str, limit: int = 20, namespace: int = 0, strict: bool = True) -> list[dict]:
    """Search MixesDB and return a list of {title, url, snippet, timestamp} dicts.

    When strict=True (default), results that don't literally contain every word
    of the query (in title or snippet) are dropped, and fetching continues until
    `limit` matching results are collected or the search is exhausted.
    """
    results = []
    offset = 0

    while len(results) < limit:
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srnamespace": namespace,
            "srlimit": MAX_PER_REQUEST,
            "sroffset": offset,
            "format": "json",
        }
        url = f"{API_URL}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        hits = data.get("query", {}).get("search", [])
        if not hits:
            break

        for hit in hits:
            title = hit["title"]
            snippet = strip_html(hit.get("snippet", ""))

            if strict and not matches_query(title, query):
                continue

            results.append(
                {
                    "title": title,
                    "url": title_to_url(title),
                    "snippet": snippet,
                    "timestamp": hit.get("timestamp", ""),
                }
            )
            if len(results) >= limit:
                break

        cont = data.get("continue", {}).get("sroffset")
        if cont is None:
            break
        offset = cont
        time.sleep(0.2)  # be polite

    return results[:limit]
