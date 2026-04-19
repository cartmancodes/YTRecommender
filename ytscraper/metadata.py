import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

import httpx
import yt_dlp

from ytscraper.models import VideoMetadata, VideoRef

_DISLIKE_API = "https://returnyoutubedislikeapi.com/votes"


def fetch(refs: list[VideoRef]) -> list[VideoMetadata]:
    results = []
    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(_fetch_one, ref): ref for ref in refs}
        for future in as_completed(futures):
            result = future.result()
            if result is not None:
                results.append(result)
    return results


def _fetch_one(ref: VideoRef) -> VideoMetadata | None:
    ydl_opts = {"quiet": True, "no_warnings": True, "skip_download": True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(ref.url, download=False)
    except Exception as exc:
        print(f"[skip] {ref.url}: {exc}", file=sys.stderr)
        return None

    dislikes, dislikes_available = _fetch_dislikes(ref.id)

    return VideoMetadata(
        id=ref.id,
        url=ref.url,
        title=info.get("title", ref.title),
        channel=info.get("channel", ""),
        duration=info.get("duration", 0),
        views=info.get("view_count", 0),
        likes=info.get("like_count", 0),
        dislikes=dislikes,
        dislikes_available=dislikes_available,
    )


def _fetch_dislikes(video_id: str) -> tuple[int, bool]:
    try:
        response = httpx.get(_DISLIKE_API, params={"videoId": video_id}, timeout=10)
        response.raise_for_status()
        return int(response.json().get("dislikes", 0)), True
    except Exception:
        return 0, False
