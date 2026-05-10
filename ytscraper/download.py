from __future__ import annotations

import sys
from pathlib import Path

import yt_dlp

AUDIO_FORMATS = {"mp3", "m4a", "opus", "wav", "flac", "aac", "vorbis"}
VIDEO_FORMATS = {"mp4", "webm", "mkv"}
NATIVE = "best"
ALL_FORMATS = AUDIO_FORMATS | VIDEO_FORMATS | {NATIVE}


def download(
    url: str,
    output_dir: Path,
    format: str = "mp3",
    audio_quality: str = "192",
) -> Path | None:
    if format not in ALL_FORMATS:
        print(
            f"[download failed] {url}: unsupported format '{format}'. "
            f"Choose from: {sorted(ALL_FORMATS)}",
            file=sys.stderr,
        )
        return None

    output_dir.mkdir(parents=True, exist_ok=True)
    ydl_opts = _build_opts(output_dir, format, audio_quality)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
    except Exception as exc:
        print(f"[download failed] {url}: {exc}", file=sys.stderr)
        return None

    return _resolve_path(ydl, info, format)


def _build_opts(output_dir: Path, format: str, audio_quality: str) -> dict:
    base = {
        "outtmpl": str(output_dir / "%(title)s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
    }

    if format in AUDIO_FORMATS:
        return {
            **base,
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": format,
                    "preferredquality": audio_quality,
                }
            ],
        }

    if format in VIDEO_FORMATS:
        return {
            **base,
            "format": f"bestvideo[ext={format}]+bestaudio/best[ext={format}]/best",
            "merge_output_format": format,
        }

    return {**base, "format": "best"}


def _resolve_path(ydl: yt_dlp.YoutubeDL, info: dict, format: str) -> Path:
    requested = info.get("requested_downloads") or []
    if requested and requested[0].get("filepath"):
        return Path(requested[0]["filepath"])

    filename = Path(ydl.prepare_filename(info))
    if format in AUDIO_FORMATS:
        filename = filename.with_suffix(f".{format}")
    return filename
