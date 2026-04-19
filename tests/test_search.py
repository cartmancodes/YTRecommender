from unittest.mock import MagicMock, patch
from ytscraper.search import search


def _make_ydl_mock(entries):
    mock = MagicMock()
    mock.__enter__ = MagicMock(return_value=mock)
    mock.__exit__ = MagicMock(return_value=False)
    mock.extract_info.return_value = {"entries": entries}
    return mock


def test_returns_video_refs():
    entries = [
        {"id": "abc123", "title": "Chill Song"},
        {"id": "def456", "title": "Another Song"},
    ]
    with patch("yt_dlp.YoutubeDL", return_value=_make_ydl_mock(entries)):
        refs = search("chill music", limit=2)
    assert len(refs) == 2
    assert refs[0].id == "abc123"
    assert refs[0].url == "https://www.youtube.com/watch?v=abc123"
    assert refs[0].title == "Chill Song"
    assert refs[1].id == "def456"


def test_empty_results():
    with patch("yt_dlp.YoutubeDL", return_value=_make_ydl_mock([])):
        refs = search("nonexistent xyzzy", limit=5)
    assert refs == []


def test_skips_entries_without_id():
    entries = [
        {"id": "abc123", "title": "Good"},
        {"title": "No ID"},
        {"id": "def456", "title": "Also Good"},
    ]
    with patch("yt_dlp.YoutubeDL", return_value=_make_ydl_mock(entries)):
        refs = search("query", limit=3)
    assert len(refs) == 2
    assert {r.id for r in refs} == {"abc123", "def456"}


def test_uses_ytsearch_url_with_limit():
    mock = _make_ydl_mock([])
    with patch("yt_dlp.YoutubeDL", return_value=mock):
        search("indie", limit=7)
    mock.extract_info.assert_called_once_with("ytsearch7:indie", download=False)
