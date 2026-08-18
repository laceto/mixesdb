"""Smoke tests for mixesdb.category (pure-logic pieces only, no network calls)."""

from mixesdb.category import url_to_category_title


def test_url_to_category_title_from_full_url():
    url = "https://www.mixesdb.com/w/Category:Richie_Hawtin"
    assert url_to_category_title(url) == "Category:Richie Hawtin"


def test_url_to_category_title_passes_through_bare_name():
    assert url_to_category_title("Category:Richie Hawtin") == "Category:Richie Hawtin"
