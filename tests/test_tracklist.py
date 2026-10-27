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


LIST_WIKITEXT = """
== Tracklist ==
<list>
;Version 1
[00] ?
...
[07] Markus Homm - Transposer [Highgrade - 134D]
--
[0:14] Igor Krsmanovic - Morocco
</list>
[[Category:2010]]
[[Category:Marco Carola]]
"""


def test_parse_tracklist_handles_list_format_without_hash():
    tracks = parse_tracklist(LIST_WIKITEXT)
    assert [t["raw"] for t in tracks] == [
        "?",
        "Markus Homm - Transposer [Highgrade - 134D]",
        "Igor Krsmanovic - Morocco",
    ]
    assert [t["timestamp"] for t in tracks] == ["00", "07", "0:14"]
    assert [t["position"] for t in tracks] == [1, 2, 3]
    assert tracks[1]["part"] == "Version 1"
    assert tracks[1]["artist"] == "Markus Homm"


def test_parse_tracklist_empty_list_and_categories_yield_no_tracks():
    wikitext = "== Tracklist ==\n<list>\n</list>\n[[Category:2006]]\n[[Category:Marco Carola]]\n"
    assert parse_tracklist(wikitext) == []
