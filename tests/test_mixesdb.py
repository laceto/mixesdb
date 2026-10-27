"""Package-level smoke test."""

import mixesdb


def test_public_api_is_importable():
    assert callable(mixesdb.search)
    assert callable(mixesdb.get_tracklist)
    assert callable(mixesdb.list_category_members)
    assert isinstance(mixesdb.__version__, str)


def test_fetch_text_retries_transient_errors(monkeypatch):
    import io
    import urllib.error

    from mixesdb import _shared

    calls = []

    def fake_urlopen(req, timeout):
        calls.append(req.full_url)
        if len(calls) < 3:
            raise urllib.error.URLError(ConnectionResetError(104, "Connection reset by peer"))
        return io.BytesIO(b"ok")

    monkeypatch.setattr(_shared.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(_shared.time, "sleep", lambda s: None)
    assert _shared.fetch_text("https://example.invalid/") == "ok"
    assert len(calls) == 3


def test_fetch_text_does_not_retry_404(monkeypatch):
    import urllib.error

    import pytest

    from mixesdb import _shared

    calls = []

    def fake_urlopen(req, timeout):
        calls.append(1)
        raise urllib.error.HTTPError(req.full_url, 404, "Not Found", {}, None)

    monkeypatch.setattr(_shared.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(_shared.time, "sleep", lambda s: None)
    with pytest.raises(urllib.error.HTTPError):
        _shared.fetch_text("https://example.invalid/")
    assert len(calls) == 1
