"""Shared constants and helpers used across mixesdb submodules."""

import time
import urllib.error
import urllib.parse
import urllib.request

API_URL = "https://www.mixesdb.com/w/api.php"
BASE_PAGE_URL = "https://www.mixesdb.com/w/"
USER_AGENT = "Mozilla/5.0 (compatible; mixesdb-scraper/1.0)"

RETRY_DELAYS = (2, 4, 8, 16)  # seconds to wait before each retry of a failed request


def fetch_text(url: str, timeout: int = 15) -> str:
    """GET `url` and return the body as text, retrying transient failures.

    Connection resets, timeouts, HTTP 429 and 5xx responses are retried with
    exponential backoff (RETRY_DELAYS); other HTTP errors (e.g. 404) raise
    immediately.
    """
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(len(RETRY_DELAYS) + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            if (e.code != 429 and e.code < 500) or attempt == len(RETRY_DELAYS):
                raise
        except (urllib.error.URLError, ConnectionError, TimeoutError):
            if attempt == len(RETRY_DELAYS):
                raise
        time.sleep(RETRY_DELAYS[attempt])


def title_to_url(title: str) -> str:
    """Reproduce MediaWiki's title -> URL mapping (spaces -> underscores, percent-encoded)."""
    return BASE_PAGE_URL + urllib.parse.quote(title.replace(" ", "_"), safe="/:@,()!'&+")
