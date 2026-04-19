from ytscraper.models import VideoRef, VideoMetadata, ScoredVideo


def test_video_ref_fields():
    ref = VideoRef(id="abc", url="https://youtu.be/abc", title="Test")
    assert ref.id == "abc"
    assert ref.url == "https://youtu.be/abc"
    assert ref.title == "Test"


def test_video_metadata_fields():
    m = VideoMetadata(
        id="abc",
        url="https://youtu.be/abc",
        title="Test",
        channel="Chan",
        duration=300,
        views=100000,
        likes=5000,
        dislikes=10,
        dislikes_available=True,
    )
    assert m.dislikes_available is True


def test_scored_video_fields():
    m = VideoMetadata(
        id="abc", url="https://youtu.be/abc", title="T", channel="C",
        duration=0, views=1, likes=1, dislikes=0, dislikes_available=False,
    )
    s = ScoredVideo(metadata=m, score=0.5)
    assert s.score == 0.5
    assert s.metadata is m
