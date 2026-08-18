"""Package-level smoke test."""

import mixesdb


def test_public_api_is_importable():
    assert callable(mixesdb.search)
    assert callable(mixesdb.get_tracklist)
    assert callable(mixesdb.list_category_members)
    assert isinstance(mixesdb.__version__, str)
