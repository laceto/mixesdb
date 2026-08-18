"""Smoke tests for mixesdb.search (pure-logic pieces only, no network calls)."""

from mixesdb.search import matches_query, strip_html
from mixesdb._shared import title_to_url


def test_matches_query_requires_every_word_in_title():
    assert matches_query("2006-08-16 - Richie Hawtin @ Cocorico, Riccione", "richie hawtin")
    assert not matches_query("2006-08-16 - Someone Else @ Cocorico, Riccione", "richie hawtin")


def test_matches_query_is_case_insensitive():
    assert matches_query("RICHIE HAWTIN", "richie hawtin")


def test_strip_html_removes_tags_and_nbsp():
    assert strip_html("<span>Richie</span>&nbsp;Hawtin") == "Richie Hawtin"


def test_title_to_url_encodes_spaces_and_special_chars():
    url = title_to_url("Sven Väth @ Cocoon")
    assert url.startswith("https://www.mixesdb.com/w/")
    assert " " not in url
    assert "_" in url
