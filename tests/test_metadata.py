import sys
from unittest.mock import MagicMock, patch
from ytscraper.models import VideoRef
from ytscraper import metadata as metadata_module


_REF_A = VideoRef(id="abc123", url="https://www.youtube.com/watch?v=abc123", title="Test A")
_REF_B = VideoRef(id="def456", url="https://www.youtube.com/watch?v=def456", title="Test B")

_YTDLP_INFO = {
    "title": "Fetched Title",
    "channel": "Test Channel",
    "duration": 240,
    "view_count": 500_000,
    "like_count": 20_000,
}


def _make_ydl_mock(info=None, raises=None):
    mock = MagicMock()
    mock.__enter__ = MagicMock(return_value=mock)
    mock.__exit__ = MagicMock(return_value=False)
    if raises:
        mock.extract_info.side_effect = raises
    else:
        mock.extract_info.return_value = info if info is not None else _YTDLP_INFO
    return mock


def _ok_dislike_response(dislikes=150):
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = {"dislikes": dislikes}
    return resp


def test_success_populates_full_metadata():
    with patch("yt_dlp.YoutubeDL", return_value=_make_ydl_mock()):
        with patch("httpx.get", return_value=_ok_dislike_response(150)):
            results = metadata_module.fetch([_REF_A])
    assert len(results) == 1
    m = results[0]
    assert m.id == "abc123"
    assert m.title == "Fetched Title"
    assert m.views == 500_000
    assert m.likes == 20_000
    assert m.dislikes == 150
    assert m.dislikes_available is True


def test_dislike_api_failure_falls_back():
    with patch("yt_dlp.YoutubeDL", return_value=_make_ydl_mock()):
        with patch("httpx.get", side_effect=Exception("API down")):
            results = metadata_module.fetch([_REF_A])
    assert len(results) == 1
    assert results[0].dislikes == 0
    assert results[0].dislikes_available is False


def test_ytdlp_failure_excludes_video():
    with patch("yt_dlp.YoutubeDL", return_value=_make_ydl_mock(raises=Exception("yt-dlp error"))):
        results = metadata_module.fetch([_REF_A])
    assert results == []


def test_ytdlp_failure_only_excludes_failing_video():
    def ydl_factory(*args, **kwargs):
        def extract_info(url, download=False):
            if "abc123" in url:
                raise Exception("fail for abc123")
            return _YTDLP_INFO
        mock = MagicMock()
        mock.__enter__ = MagicMock(return_value=mock)
        mock.__exit__ = MagicMock(return_value=False)
        mock.extract_info = extract_info
        return mock

    with patch("yt_dlp.YoutubeDL", side_effect=ydl_factory):
        with patch("httpx.get", return_value=_ok_dislike_response()):
            results = metadata_module.fetch([_REF_A, _REF_B])
    assert len(results) == 1
    assert results[0].id == "def456"


def test_none_metadata_fields_coerced_to_defaults():
    info = {
        "title": None,
        "channel": None,
        "duration": None,
        "view_count": None,
        "like_count": None,
    }
    with patch("yt_dlp.YoutubeDL", return_value=_make_ydl_mock(info=info)):
        with patch("httpx.get", return_value=_ok_dislike_response(150)):
            results = metadata_module.fetch([_REF_A])
    assert len(results) == 1
    m = results[0]
    assert m.title == "Test A"
    assert m.channel == ""
    assert m.duration == 0
    assert m.views == 0
    assert m.likes == 0


def test_dislike_api_called_with_correct_video_id():
    with patch("yt_dlp.YoutubeDL", return_value=_make_ydl_mock()):
        with patch("httpx.get", return_value=_ok_dislike_response()) as mock_get:
            metadata_module.fetch([_REF_A])
    call_kwargs = mock_get.call_args
    assert call_kwargs.kwargs["params"] == {"videoId": "abc123"}
