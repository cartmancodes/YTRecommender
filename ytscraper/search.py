import yt_dlp
from ytscraper.models import VideoRef


def search(query: str, limit: int = 10) -> list[VideoRef]:
    ydl_opts = {
        "quiet": True,
        "extract_flat": True,
        "skip_download": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
    return [
        VideoRef(
            id=e["id"],
            url=f"https://www.youtube.com/watch?v={e['id']}",
            title=e.get("title", ""),
        )
        for e in info.get("entries", [])
        if e.get("id")
    ]
