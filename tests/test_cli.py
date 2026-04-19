import json
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
