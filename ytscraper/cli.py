from __future__ import annotations

import argparse
import json
import sys

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
        description="Fetch and rank YouTube videos by quality.",
    )
    p.add_argument("-c", "--content", required=True, help="Search query")
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
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

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

    return 0


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
