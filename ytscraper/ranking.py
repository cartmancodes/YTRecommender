from ytscraper.models import VideoMetadata, ScoredVideo


def filter_and_rank(
    videos: list[VideoMetadata],
    min_views: int = 10_000,
    min_like_ratio: float = 100.0,
) -> list[ScoredVideo]:
    results = []
    for v in videos:
        if v.views < min_views:
            continue
        if v.dislikes_available and v.dislikes > 0 and (v.likes / v.dislikes) < min_like_ratio:
            continue
        score = (v.likes / max(v.dislikes, 1)) * (v.likes / max(v.views, 1))
        results.append(ScoredVideo(metadata=v, score=score))
    results.sort(key=lambda s: s.score, reverse=True)
    return results
