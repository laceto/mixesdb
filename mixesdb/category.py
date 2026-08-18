"""List all mix pages under a MixesDB category.

Uses the MediaWiki action API (list=categorymembers) to enumerate every
page in a category, e.g. https://www.mixesdb.com/w/Category:Richie_Hawtin
"""

import json
import time
import urllib.parse
import urllib.request

from ._shared import API_URL, USER_AGENT, title_to_url

MAX_PER_REQUEST = 500


def url_to_category_title(value: str) -> str:
    """Accept either a full category URL or a bare 'Category:Name' string."""
    if value.startswith("http"):
        path = urllib.parse.urlparse(value).path
        title = path.split("/w/", 1)[-1]
        return urllib.parse.unquote(title).replace("_", " ")
    return value


def list_category_members(category: str, limit: int | None = None) -> list[dict]:
    """Return [{title, url}] for every page in the category (subcategories excluded)."""
    cmtitle = category if category.startswith("Category:") else f"Category:{category}"
    members = []
    cmcontinue = None

    while True:
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": cmtitle,
            "cmlimit": MAX_PER_REQUEST,
            "cmtype": "page",
            "format": "json",
        }
        if cmcontinue:
            params["cmcontinue"] = cmcontinue

        url = f"{API_URL}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        for m in data.get("query", {}).get("categorymembers", []):
            members.append({"title": m["title"], "url": title_to_url(m["title"])})
            if limit and len(members) >= limit:
                return members

        cmcontinue = data.get("continue", {}).get("cmcontinue")
        if not cmcontinue:
            break
        time.sleep(0.2)

    return members
