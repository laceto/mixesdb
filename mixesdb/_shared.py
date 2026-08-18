"""Shared constants and helpers used across mixesdb submodules."""

import urllib.parse

API_URL = "https://www.mixesdb.com/w/api.php"
BASE_PAGE_URL = "https://www.mixesdb.com/w/"
USER_AGENT = "Mozilla/5.0 (compatible; mixesdb-scraper/1.0)"


def title_to_url(title: str) -> str:
    """Reproduce MediaWiki's title -> URL mapping (spaces -> underscores, percent-encoded)."""
    return BASE_PAGE_URL + urllib.parse.quote(title.replace(" ", "_"), safe="/:@,()!'&+")
