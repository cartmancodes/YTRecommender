import json
from pathlib import Path
from unittest.mock import patch

from ytscraper.cli import main
from ytscraper.models import VideoMetadata, VideoRef, ScoredVideo


def _meta(**kwargs):
    defaults = dict(
        id="abc123",
        url="https://youtu.be/abc123",
        title="Chill Indie Video",
        channel="Indie Channel",
        duration=300,
        views=500_000,
        likes=25_000,
        dislikes=50,
        dislikes_available=True,
    )
    defaults.update(kwargs)
    return VideoMetadata(**defaults)


def _scored(score=0.421, **kwargs):
    return ScoredVideo(metadata=_meta(**kwargs), score=score)


def _patch_pipeline(ranked):
    refs = [VideoRef("abc123", "https://youtu.be/abc123", "Chill Indie Video")]
    return (
        patch("ytscraper.cli.search", return_value=refs),
        patch("ytscraper.cli.fetch", return_value=[ranked[0].metadata] if ranked else []),
        patch("ytscraper.cli.filter_and_rank", return_value=ranked),
    )


def test_table_output_exits_zero(capsys):
    scored = [_scored()]
    p1, p2, p3 = _patch_pipeline(scored)
    with p1, p2, p3:
        code = main(["-c", "indie"])
    assert code == 0
    out = capsys.readouterr().out
    assert "Score" in out
    assert "Chill Indie Video" in out
    assert "https://youtu.be/abc123" in out


def test_json_output_is_valid_json(capsys):
    scored = [_scored(score=0.421)]
    p1, p2, p3 = _patch_pipeline(scored)
    with p1, p2, p3:
        code = main(["-c", "indie", "--json"])
    assert code == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert len(data) == 1
    assert data[0]["url"] == "https://youtu.be/abc123"
    assert data[0]["score"] == 0.421
    assert data[0]["dislikes_available"] is True


def test_no_search_results_exits_nonzero(capsys):
    with patch("ytscraper.cli.search", return_value=[]):
        code = main(["-c", "indie"])
    assert code == 1
    assert "No results" in capsys.readouterr().err


def test_no_metadata_exits_nonzero(capsys):
    refs = [VideoRef("abc123", "https://youtu.be/abc123", "T")]
    with patch("ytscraper.cli.search", return_value=refs):
        with patch("ytscraper.cli.fetch", return_value=[]):
            code = main(["-c", "indie"])
    assert code == 1
    assert "No metadata" in capsys.readouterr().err


def test_top_flag_limits_output(capsys):
    scored = [_scored(score=0.9), _scored(id="def456", url="https://youtu.be/def456", score=0.5)]
    p1, p2, p3 = _patch_pipeline(scored)
    with p1, p2, p3:
        code = main(["-c", "indie", "--top", "1"])
    assert code == 0
    out = capsys.readouterr().out
    assert out.count("youtu.be") == 1


def test_dislikes_unavailable_shows_asterisk(capsys):
    scored = [_scored(dislikes=0, dislikes_available=False)]
    p1, p2, p3 = _patch_pipeline(scored)
    with p1, p2, p3:
        code = main(["-c", "indie"])
    assert code == 0
    out = capsys.readouterr().out
    assert "*" in out


def test_missing_content_and_url_exits_with_usage_error(capsys):
    code = main([])
    assert code == 2
    assert "content" in capsys.readouterr().err.lower()


def test_url_flag_downloads_directly_and_skips_search(tmp_path, capsys):
    saved = tmp_path / "song.mp3"
    with patch("ytscraper.cli.download", return_value=saved) as dl, \
         patch("ytscraper.cli.search") as srch:
        code = main(["--url", "https://youtu.be/abc", "--output-dir", str(tmp_path), "--format", "mp3"])
    assert code == 0
    srch.assert_not_called()
    dl.assert_called_once_with("https://youtu.be/abc", Path(str(tmp_path)), "mp3", "192")
    assert "Saved" in capsys.readouterr().out


def test_url_download_failure_returns_nonzero(tmp_path):
    with patch("ytscraper.cli.download", return_value=None):
        code = main(["--url", "https://youtu.be/x", "--output-dir", str(tmp_path)])
    assert code == 1


def test_download_flag_downloads_each_ranked_video(tmp_path, capsys):
    scored = [
        _scored(score=0.9),
        _scored(id="def456", url="https://youtu.be/def456", score=0.5),
    ]
    p1, p2, p3 = _patch_pipeline(scored)
    with p1, p2, p3, patch(
        "ytscraper.cli.download",
        side_effect=[tmp_path / "a.mp3", tmp_path / "b.mp3"],
    ) as dl:
        code = main(["-c", "indie", "--download", "--output-dir", str(tmp_path)])
    assert code == 0
    assert dl.call_count == 2
    assert "Downloading 2 video(s)" in capsys.readouterr().out


def test_download_flag_returns_nonzero_when_all_fail(tmp_path):
    scored = [_scored()]
    p1, p2, p3 = _patch_pipeline(scored)
    with p1, p2, p3, patch("ytscraper.cli.download", return_value=None):
        code = main(["-c", "indie", "--download", "--output-dir", str(tmp_path)])
    assert code == 1


def test_invalid_format_rejected_by_argparse(capsys):
    try:
        main(["--url", "https://youtu.be/x", "--format", "aiff"])
    except SystemExit as e:
        assert e.code == 2
    assert "invalid choice" in capsys.readouterr().err
