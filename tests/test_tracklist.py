"""Smoke tests for mixesdb.tracklist (pure-logic pieces only, no network calls)."""

from mixesdb.tracklist import clean_wikitext, parse_tracklist, url_to_title

SAMPLE_WIKITEXT = """
Some intro text.

== Tracklist ==
;Part 1
# [00:00] Richie Hawtin - Spastik
# [04:12] Underworld - Two Months Off

== Credits ==
Some other section.
"""


def test_url_to_title_decodes_path():
    url = "https://www.mixesdb.com/w/2006-08-16_-_Richie_Hawtin_@_Cocorico"
    assert url_to_title(url) == "2006-08-16_-_Richie_Hawtin_@_Cocorico"


def test_clean_wikitext_strips_links_templates_and_markup():
    assert clean_wikitext("[[Richie Hawtin]] plays '''Spastik''' {{cite}}") == "Richie Hawtin plays Spastik"


def test_parse_tracklist_extracts_part_and_tracks():
    tracks = parse_tracklist(SAMPLE_WIKITEXT)
    assert len(tracks) == 2
    assert tracks[0] == {
        "part": "Part 1",
        "position": 1,
        "timestamp": "00:00",
        "artist": "Richie Hawtin",
        "title": "Spastik",
        "raw": "Richie Hawtin - Spastik",
    }


def test_parse_tracklist_returns_empty_list_without_section():
    assert parse_tracklist("No tracklist here.") == []
