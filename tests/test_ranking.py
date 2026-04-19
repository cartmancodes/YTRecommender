from ytscraper.models import VideoMetadata, ScoredVideo
from ytscraper.ranking import filter_and_rank


def _make(
    id="abc",
    views=100_000,
    likes=5_000,
    dislikes=10,
    dislikes_available=True,
):
    return VideoMetadata(
        id=id,
        url=f"https://www.youtube.com/watch?v={id}",
        title="Test Video",
        channel="Test Channel",
        duration=300,
        views=views,
        likes=likes,
        dislikes=dislikes,
        dislikes_available=dislikes_available,
    )


def test_filters_below_min_views():
    videos = [_make(views=5_000)]
    assert filter_and_rank(videos, min_views=10_000, min_like_ratio=100) == []


def test_passes_video_meeting_min_views():
    videos = [_make(views=50_000, likes=5_000, dislikes=10)]
    result = filter_and_rank(videos, min_views=10_000, min_like_ratio=100)
    assert len(result) == 1


def test_filters_below_min_like_ratio():
    # likes=100, dislikes=10 → ratio=10, below threshold of 100
    videos = [_make(views=50_000, likes=100, dislikes=10)]
    assert filter_and_rank(videos, min_views=10_000, min_like_ratio=100) == []


def test_skips_like_ratio_when_dislikes_unavailable():
    # Would fail ratio filter (likes=100, dislikes=0 means unavailable fallback)
    # but dislikes_available=False so ratio check is skipped
    videos = [_make(views=50_000, likes=100, dislikes=0, dislikes_available=False)]
    result = filter_and_rank(videos, min_views=10_000, min_like_ratio=100)
    assert len(result) == 1


def test_zero_dislikes_available_no_zerodivision():
    # dislikes=0, dislikes_available=True → treat as excellent ratio
    videos = [_make(views=50_000, likes=5_000, dislikes=0, dislikes_available=True)]
    result = filter_and_rank(videos, min_views=10_000, min_like_ratio=100)
    assert len(result) == 1
    assert result[0].score > 0


def test_sorts_descending_by_score():
    low = _make(id="low", views=1_000_000, likes=1_000, dislikes=100)
    high = _make(id="high", views=100_000, likes=10_000, dislikes=10)
    result = filter_and_rank([low, high], min_views=10_000, min_like_ratio=0)
    assert result[0].metadata.id == "high"
    assert result[0].score > result[1].score


def test_score_formula():
    # score = (likes / max(dislikes,1)) * (likes / max(views,1))
    # likes=100, dislikes=10, views=1000 → (100/10) * (100/1000) = 10 * 0.1 = 1.0
    videos = [_make(views=1_000, likes=100, dislikes=10)]
    result = filter_and_rank(videos, min_views=0, min_like_ratio=0)
    assert abs(result[0].score - 1.0) < 1e-9


def test_empty_input():
    assert filter_and_rank([], min_views=10_000, min_like_ratio=100) == []
