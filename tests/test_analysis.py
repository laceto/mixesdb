"""Tests for the pure helpers in analysis/ (no data files needed)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "analysis"))

from common import clean, identified, is_self_play, key, split_artists  # noqa: E402
from locations import locate  # noqa: E402


def row(artist, title):
    return {"artist": artist, "title": title}


def test_key_ignores_spacing_and_punctuation():
    assert key("Lemon 8 - Model 8") == key("Lemon8 – Model8")


def test_clean_strips_label_and_layer_marker():
    assert clean("+ Basti Grub - Swing It [Cécille - CEC 005]") == "Basti Grub - Swing It"


def test_split_artists_credits_every_collaborator():
    assert split_artists("Basti Grub & Aldo Cadiz feat. Agent!") == ["Basti Grub", "Aldo Cadiz", "Agent!"]
    assert split_artists("2000 and One") == ["2000 and One"]


def test_identified_rejects_placeholders():
    assert identified(row("Lemos", "Blow It"))
    assert not identified(row("?", "?"))
    assert not identified(row("ID", "ID"))


def test_is_self_play_covers_aliases_and_remixes():
    assert is_self_play("richie_hawtin", row("Plastikman", "Spastik"))
    assert is_self_play("paul_kalkbrenner", row("Stromae", "Te Quiero (Paul Kalkbrenner Remix)"))
    assert not is_self_play("richie_hawtin", row("Marco Carola", "Jackpot"))


def test_locate_reads_city_country_and_implied_venues():
    assert locate("2008-04-05 - Nick Curly @ Time Warp, Mannheim, Germany") == ("Time Warp", "Mannheim", "Germany")
    assert locate("2005-08-21 - Tania Vulcano @ Circo Loco, DC10, Ibiza - Essential Mix")[1:] == ("Ibiza", "Spain")
    assert locate("2013-03-23 - Luciano @ Ultra Music Festival, WMC")[1:] == ("Miami", "USA")
    assert locate("2008-05-24 - Nick Curly - Clubnight") == (None, None, None)
