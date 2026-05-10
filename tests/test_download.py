from pathlib import Path
from unittest.mock import MagicMock, patch

from ytscraper.download import ALL_FORMATS, _build_opts, download


def test_audio_format_uses_extract_audio_postprocessor():
    opts = _build_opts(Path("/tmp/out"), "mp3", "192")
    assert opts["format"] == "bestaudio/best"
    pps = opts["postprocessors"]
    assert len(pps) == 1
    assert pps[0]["key"] == "FFmpegExtractAudio"
    assert pps[0]["preferredcodec"] == "mp3"
    assert pps[0]["preferredquality"] == "192"


def test_video_format_sets_merge_format_and_no_postprocessor():
    opts = _build_opts(Path("/tmp/out"), "mp4", "192")
    assert opts["merge_output_format"] == "mp4"
    assert "postprocessors" not in opts
    assert "ext=mp4" in opts["format"]


def test_native_best_uses_no_conversion():
    opts = _build_opts(Path("/tmp/out"), "best", "192")
    assert opts["format"] == "best"
    assert "postprocessors" not in opts
    assert "merge_output_format" not in opts


def test_unsupported_format_returns_none(capsys):
    result = download("https://youtu.be/x", Path("/tmp/out"), format="aiff")
    assert result is None
    err = capsys.readouterr().err
    assert "unsupported format" in err


def test_download_returns_filepath_from_requested_downloads(tmp_path):
    fake_path = tmp_path / "Some Title.mp3"
    info = {"requested_downloads": [{"filepath": str(fake_path)}]}

    with patch("ytscraper.download.yt_dlp.YoutubeDL") as ydl_cls:
        ydl = MagicMock()
        ydl.extract_info.return_value = info
        ydl_cls.return_value.__enter__.return_value = ydl

        result = download("https://youtu.be/abc", tmp_path, "mp3")

    assert result == fake_path


def test_download_falls_back_to_prepare_filename_with_audio_suffix(tmp_path):
    info = {}  # no requested_downloads

    with patch("ytscraper.download.yt_dlp.YoutubeDL") as ydl_cls:
        ydl = MagicMock()
        ydl.extract_info.return_value = info
        ydl.prepare_filename.return_value = str(tmp_path / "Title.webm")
        ydl_cls.return_value.__enter__.return_value = ydl

        result = download("https://youtu.be/abc", tmp_path, "mp3")

    assert result == tmp_path / "Title.mp3"


def test_download_handles_yt_dlp_exception(tmp_path, capsys):
    with patch("ytscraper.download.yt_dlp.YoutubeDL") as ydl_cls:
        ydl = MagicMock()
        ydl.extract_info.side_effect = RuntimeError("boom")
        ydl_cls.return_value.__enter__.return_value = ydl

        result = download("https://youtu.be/abc", tmp_path, "mp3")

    assert result is None
    assert "boom" in capsys.readouterr().err


def test_supported_formats_include_common_audio_and_video():
    for f in ("mp3", "m4a", "opus", "wav", "flac", "mp4", "webm", "mkv", "best"):
        assert f in ALL_FORMATS
