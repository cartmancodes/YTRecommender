from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ytscraper.download import ALL_FORMATS, download
from ytscraper.metadata import fetch
from ytscraper.models import ScoredVideo
from ytscraper.ranking import filter_and_rank
from ytscraper.search import search


def _fmt(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.0f}K"
    return str(n)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ytscraper",
        description="Fetch and rank YouTube videos by quality, and optionally download them.",
    )
    p.add_argument("-c", "--content", help="Search query (omit when using --url)")
    p.add_argument(
        "-p", "--pages", type=int, default=10,
        help="Number of candidates to fetch (default: 10)",
    )
    p.add_argument("--min-views", type=int, default=10_000, help="Minimum views (default: 10000)")
    p.add_argument(
        "--min-like-ratio", type=float, default=100.0,
        help="Minimum likes/dislikes ratio (default: 100)",
    )
    p.add_argument("--top", type=int, default=None, help="Number of results to show (default: all)")
    p.add_argument("--json", action="store_true", help="Output as JSON array")
    p.add_argument(
        "--download", action="store_true",
        help="Download the ranked results (or the --url target)",
    )
    p.add_argument(
        "--url",
        help="Download a specific YouTube URL directly (bypasses search; implies --download)",
    )
    p.add_argument(
        "--format", default="mp3", choices=sorted(ALL_FORMATS),
        help="Download format (default: mp3). Audio formats require ffmpeg installed.",
    )
    p.add_argument(
        "--output-dir", default="./downloads",
        help="Directory for downloads (default: ./downloads)",
    )
    p.add_argument(
        "--audio-quality", default="192",
        help="Audio bitrate in kbps for lossy audio formats (default: 192)",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    if not args.content and not args.url:
        print("Error: provide -c/--content for search or --url to download a link directly.", file=sys.stderr)
        return 2

    output_dir = Path(args.output_dir)

    if args.url:
        result = download(args.url, output_dir, args.format, args.audio_quality)
        if result is None:
            return 1
        print(f"Saved: {result}")
        return 0

    refs = search(args.content, args.pages)
    if not refs:
        print("No results found.", file=sys.stderr)
        return 1

    videos = fetch(refs)
    if not videos:
        print("No metadata extractable.", file=sys.stderr)
        return 1

    ranked = filter_and_rank(videos, args.min_views, args.min_like_ratio)
    if args.top is not None:
        ranked = ranked[: args.top]

    if args.json:
        _output_json(ranked)
    else:
        _output_table(ranked)

    if args.download:
        return _download_ranked(ranked, output_dir, args.format, args.audio_quality)

    return 0


def _download_ranked(
    ranked: list[ScoredVideo], output_dir: Path, format: str, audio_quality: str
) -> int:
    if not ranked:
        return 0
    print(f"\nDownloading {len(ranked)} video(s) to {output_dir}/ as {format}...")
    successes = 0
    for s in ranked:
        result = download(s.metadata.url, output_dir, format, audio_quality)
        if result is not None:
            successes += 1
            print(f"Saved: {result}")
    return 0 if successes else 1


def _output_json(ranked: list[ScoredVideo]) -> None:
    out = [
        {
            "url": s.metadata.url,
            "title": s.metadata.title,
            "views": s.metadata.views,
            "likes": s.metadata.likes,
            "dislikes": s.metadata.dislikes,
            "dislikes_available": s.metadata.dislikes_available,
            "score": round(s.score, 4),
        }
        for s in ranked
    ]
    print(json.dumps(out, indent=2))


def _output_table(ranked: list[ScoredVideo]) -> None:
    if not ranked:
        print("No videos passed the quality filter.")
        return
    header = (
        f" {'#':>2}  {'Score':<7} {'Views':<8} {'Likes':<7} {'Dislikes':<9}"
        f" {'Title':<35} URL"
    )
    print(header)
    for i, s in enumerate(ranked, 1):
        m = s.metadata
        dislikes_str = _fmt(m.dislikes) + ("" if m.dislikes_available else "*")
        print(
            f" {i:>2}  {s.score:<7.3f} {_fmt(m.views):<8} {_fmt(m.likes):<7}"
            f" {dislikes_str:<9} {m.title[:35]:<35} {m.url}"
        )
