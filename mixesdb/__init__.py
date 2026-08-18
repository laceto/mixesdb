"""mixesdb — scraper toolkit for MixesDB (mixesdb.com), talking directly to its
MediaWiki `action=api.php` and `action=raw` endpoints.
"""

from ._shared import title_to_url
from .category import list_category_members, url_to_category_title
from .search import matches_query, search
from .tracklist import (
    extract_tracklist_section,
    fetch_raw_wikitext,
    get_tracklist,
    parse_tracklist,
    url_to_title,
)

__version__ = "0.1.0"

__all__ = [
    "search",
    "matches_query",
    "list_category_members",
    "url_to_category_title",
    "get_tracklist",
    "parse_tracklist",
    "fetch_raw_wikitext",
    "extract_tracklist_section",
    "url_to_title",
    "title_to_url",
]
