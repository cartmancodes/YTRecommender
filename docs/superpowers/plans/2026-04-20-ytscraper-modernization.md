# YTscraper Modernization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the broken 2021 HTML-scraping stack with yt-dlp + Return YouTube Dislike API, rename the package to `ytscraper/`, and deliver a ranked filtered list of YouTube videos scored by quality.

**Architecture:** Data flows one direction through four focused modules — `search.py` fetches candidate video refs via yt-dlp, `metadata.py` enriches them concurrently (yt-dlp for views/likes + Return YouTube Dislike API for dislikes), `ranking.py` filters and sorts by quality score, and `cli.py` wires everything together and handles output. All shared types live in `models.py`.

**Tech Stack:** Python ≥ 3.11, `yt-dlp`, `httpx`, `pytest`, `concurrent.futures.ThreadPoolExecutor`.

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Delete | `YTlib/` | Entire old package — nothing worth preserving |
| Create | `ytscraper/__init__.py` | Package marker (empty) |
| Create | `ytscraper/__main__.py` | `python -m ytscraper` entry point |
| Create | `ytscraper/models.py` | `VideoRef`, `VideoMetadata`, `ScoredVideo` dataclasses |
| Create | `ytscraper/search.py` | `search(query, limit) -> list[VideoRef]` |
| Create | `ytscraper/metadata.py` | `fetch(refs) -> list[VideoMetadata]` (concurrent) |
| Create | `ytscraper/ranking.py` | `filter_and_rank(videos, min_views, min_like_ratio) -> list[ScoredVideo]` |
| Create | `ytscraper/cli.py` | argparse, pipeline orchestration, table/JSON output |
| Replace | `requirements.txt` | `yt-dlp`, `httpx`, `pytest` — all 2021 deps removed |
| Create | `.python-version` | `3.11` |
| Update | `README.md` | New invocation, Python requirement, API note |
| Create | `tests/__init__.py` | Package marker (empty) |
| Create | `tests/test_models.py` | Import smoke tests for dataclasses |
| Create | `tests/test_ranking.py` | Unit tests for `filter_and_rank` (pure function) |
| Create | `tests/test_search.py` | Unit tests for `search` (yt-dlp mocked) |
| Create | `tests/test_metadata.py` | Unit tests for `fetch` (yt-dlp + httpx mocked) |
| Create | `tests/test_cli.py` | Smoke tests for table + JSON output |

---

## Task 1: Scaffold — replace dependencies, delete YTlib, create package skeletons

**Files:**
- Delete: `YTlib/`
- Replace: `requirements.txt`
- Create: `.python-version`
- Create: `ytscraper/__init__.py`
- Create: `ytscraper/__main__.py` (stub)
- Create: `tests/__init__.py`

- [ ] **Step 1: Replace requirements.txt**

Overwrite the file with exactly:

```
yt-dlp
httpx
pytest
```

- [ ] **Step 2: Create .python-version**

```
3.11
```

- [ ] **Step 3: Delete YTlib/**

```bash
rm -rf YTlib/
```

- [ ] **Step 4: Create ytscraper/ package with stub __main__.py**

```bash
mkdir -p ytscraper tests
touch ytscraper/__init__.py tests/__init__.py
```

Create `ytscraper/__main__.py`:

```python
import sys
from ytscraper.cli import main

sys.exit(main())
```

- [ ] **Step 5: Install new dependencies**

```bash
pip install -r requirements.txt
```

Expected: all three packages install without error.

- [ ] **Step 6: Verify package is importable**

```bash
python -c "import ytscraper; print('ok')"
```

Expected: `ok`

- [ ] **Step 7: Commit**

```bash
git add ytscraper/ tests/ requirements.txt .python-version
git rm -r YTlib/
git commit -m "chore: scaffold ytscraper package, drop YTlib and 2021 deps"
```

---

## Task 2: Models — shared dataclasses

**Files:**
- Create: `ytscraper/models.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_models.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_models.py -v
```

Expected: `ImportError` — `ytscraper.models` not found.

- [ ] **Step 3: Implement ytscraper/models.py**

```python
from dataclasses import dataclass


@dataclass
class VideoRef:
    id: str
    url: str
    title: str


@dataclass
class VideoMetadata:
    id: str
    url: str
    title: str
    channel: str
    duration: int
    views: int
    likes: int
    dislikes: int
    dislikes_available: bool


@dataclass
class ScoredVideo:
    metadata: VideoMetadata
    score: float
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_models.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add ytscraper/models.py tests/test_models.py
git commit -m "feat: add VideoRef, VideoMetadata, ScoredVideo dataclasses"
```

---

## Task 3: Ranking — filter_and_rank (pure function, fully testable)

**Files:**
- Create: `ytscraper/ranking.py`
- Create: `tests/test_ranking.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_ranking.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_ranking.py -v
```

Expected: `ImportError` — `ytscraper.ranking` not found.

- [ ] **Step 3: Implement ytscraper/ranking.py**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_ranking.py -v
```

Expected: 8 passed.

- [ ] **Step 5: Commit**

```bash
git add ytscraper/ranking.py tests/test_ranking.py
git commit -m "feat: implement filter_and_rank with quality score"
```

---

## Task 4: Search — yt-dlp search wrapper

**Files:**
- Create: `ytscraper/search.py`
- Create: `tests/test_search.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_search.py`:

```python
from unittest.mock import MagicMock, patch
from ytscraper.search import search


def _make_ydl_mock(entries):
    mock = MagicMock()
    mock.__enter__ = MagicMock(return_value=mock)
    mock.__exit__ = MagicMock(return_value=False)
    mock.extract_info.return_value = {"entries": entries}
    return mock


def test_returns_video_refs():
    entries = [
        {"id": "abc123", "title": "Chill Song"},
        {"id": "def456", "title": "Another Song"},
    ]
    with patch("yt_dlp.YoutubeDL", return_value=_make_ydl_mock(entries)):
        refs = search("chill music", limit=2)
    assert len(refs) == 2
    assert refs[0].id == "abc123"
    assert refs[0].url == "https://www.youtube.com/watch?v=abc123"
    assert refs[0].title == "Chill Song"
    assert refs[1].id == "def456"


def test_empty_results():
    with patch("yt_dlp.YoutubeDL", return_value=_make_ydl_mock([])):
        refs = search("nonexistent xyzzy", limit=5)
    assert refs == []


def test_skips_entries_without_id():
    entries = [
        {"id": "abc123", "title": "Good"},
        {"title": "No ID"},
        {"id": "def456", "title": "Also Good"},
    ]
    with patch("yt_dlp.YoutubeDL", return_value=_make_ydl_mock(entries)):
        refs = search("query", limit=3)
    assert len(refs) == 2
    assert {r.id for r in refs} == {"abc123", "def456"}


def test_uses_ytsearch_url_with_limit():
    mock = _make_ydl_mock([])
    with patch("yt_dlp.YoutubeDL", return_value=mock) as ydl_cls:
        search("indie", limit=7)
    mock.extract_info.assert_called_once_with("ytsearch7:indie", download=False)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_search.py -v
```

Expected: `ImportError` — `ytscraper.search` not found.

- [ ] **Step 3: Implement ytscraper/search.py**

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_search.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add ytscraper/search.py tests/test_search.py
git commit -m "feat: implement search() via yt-dlp ytsearchN extractor"
```

---

## Task 5: Metadata — concurrent yt-dlp + Return YouTube Dislike API fetch

**Files:**
- Create: `ytscraper/metadata.py`
- Create: `tests/test_metadata.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_metadata.py`:

```python
import sys
from unittest.mock import MagicMock, patch
from ytscraper.models import VideoRef
from ytscraper import metadata as metadata_module


_REF_A = VideoRef(id="abc123", url="https://www.youtube.com/watch?v=abc123", title="Test A")
_REF_B = VideoRef(id="def456", url="https://www.youtube.com/watch?v=def456", title="Test B")

_YTDLP_INFO = {
    "title": "Fetched Title",
    "channel": "Test Channel",
    "duration": 240,
    "view_count": 500_000,
    "like_count": 20_000,
}


def _make_ydl_mock(info=None, raises=None):
    mock = MagicMock()
    mock.__enter__ = MagicMock(return_value=mock)
    mock.__exit__ = MagicMock(return_value=False)
    if raises:
        mock.extract_info.side_effect = raises
    else:
        mock.extract_info.return_value = info if info is not None else _YTDLP_INFO
    return mock


def _ok_dislike_response(dislikes=150):
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = {"dislikes": dislikes}
    return resp


def test_success_populates_full_metadata():
    with patch("yt_dlp.YoutubeDL", return_value=_make_ydl_mock()):
        with patch("httpx.get", return_value=_ok_dislike_response(150)):
            results = metadata_module.fetch([_REF_A])
    assert len(results) == 1
    m = results[0]
    assert m.id == "abc123"
    assert m.title == "Fetched Title"
    assert m.views == 500_000
    assert m.likes == 20_000
    assert m.dislikes == 150
    assert m.dislikes_available is True


def test_dislike_api_failure_falls_back():
    with patch("yt_dlp.YoutubeDL", return_value=_make_ydl_mock()):
        with patch("httpx.get", side_effect=Exception("API down")):
            results = metadata_module.fetch([_REF_A])
    assert len(results) == 1
    assert results[0].dislikes == 0
    assert results[0].dislikes_available is False


def test_ytdlp_failure_excludes_video():
    with patch("yt_dlp.YoutubeDL", return_value=_make_ydl_mock(raises=Exception("yt-dlp error"))):
        results = metadata_module.fetch([_REF_A])
    assert results == []


def test_ytdlp_failure_only_excludes_failing_video():
    def ydl_factory(*args, **kwargs):
        def extract_info(url, download=False):
            if "abc123" in url:
                raise Exception("fail for abc123")
            return _YTDLP_INFO
        mock = MagicMock()
        mock.__enter__ = MagicMock(return_value=mock)
        mock.__exit__ = MagicMock(return_value=False)
        mock.extract_info = extract_info
        return mock

    with patch("yt_dlp.YoutubeDL", side_effect=ydl_factory):
        with patch("httpx.get", return_value=_ok_dislike_response()):
            results = metadata_module.fetch([_REF_A, _REF_B])
    assert len(results) == 1
    assert results[0].id == "def456"


def test_dislike_api_called_with_correct_video_id():
    with patch("yt_dlp.YoutubeDL", return_value=_make_ydl_mock()):
        with patch("httpx.get", return_value=_ok_dislike_response()) as mock_get:
            metadata_module.fetch([_REF_A])
    call_kwargs = mock_get.call_args
    assert call_kwargs.kwargs["params"] == {"videoId": "abc123"}
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_metadata.py -v
```

Expected: `ImportError` — `ytscraper.metadata` not found.

- [ ] **Step 3: Implement ytscraper/metadata.py**

```python
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
    ydl_opts = {"quiet": True, "skip_download": True}
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_metadata.py -v
```

Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add ytscraper/metadata.py tests/test_metadata.py
git commit -m "feat: implement concurrent metadata fetch with Return YouTube Dislike API"
```

---

## Task 6: CLI — argparse, pipeline orchestration, table + JSON output

**Files:**
- Create: `ytscraper/cli.py`
- Create: `tests/test_cli.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_cli.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_cli.py -v
```

Expected: `ImportError` — `ytscraper.cli` not found.

- [ ] **Step 3: Implement ytscraper/cli.py**

```python
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
        help="Minimum likes/dislikes ratio (default: 100, skipped when dislikes unavailable)",
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_cli.py -v
```

Expected: 6 passed.

- [ ] **Step 5: Run the full test suite**

```bash
pytest -v
```

Expected: all tests pass (test_models, test_ranking, test_search, test_metadata, test_cli).

- [ ] **Step 6: Smoke-test the CLI help**

```bash
python -m ytscraper --help
```

Expected output includes `-c/--content`, `-p/--pages`, `--min-views`, `--min-like-ratio`, `--top`, `--json`.

- [ ] **Step 7: Commit**

```bash
git add ytscraper/cli.py tests/test_cli.py
git commit -m "feat: implement CLI with table and JSON output"
```

---

## Task 7: README update

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Rewrite README.md**

Replace the entire file with:

```markdown
# YTscraper

Fetch and rank YouTube videos by quality — filtered by views and like/dislike ratio, sorted by a quality score.

**Requires Python 3.11+**

> Dislike counts are sourced from the [Return YouTube Dislike API](https://returnyoutubedislikeapi.com/), a community-maintained service. They are estimates, not the original YouTube counts (YouTube removed public dislike counts in November 2021).

## Setup

```bash
pip install -r requirements.txt
```

## Usage

```bash
python -m ytscraper -c "chill indie playlist" -p 20
```

| Flag | Default | Description |
|------|---------|-------------|
| `-c`, `--content` | required | Search query |
| `-p`, `--pages` | `10` | Number of candidates to search |
| `--min-views` | `10000` | Minimum view count |
| `--min-like-ratio` | `100` | Minimum likes/dislikes ratio |
| `--top` | all | Limit number of results shown |
| `--json` | off | Output as JSON instead of table |

## Example

```bash
python -m ytscraper -c "lo-fi beats" -p 15 --top 5
```

```
 #  Score   Views    Likes   Dislikes  Title                               URL
 1  0.521   2.1M     180K    210       Lo-Fi Study Beats 2025              https://www.youtube.com/watch?v=...
 2  0.418   890K     72K     95        Chill Lofi Radio                    https://www.youtube.com/watch?v=...
```

A `*` after the Dislikes value means the Return YouTube Dislike API was unavailable for that video; the like/dislike ratio filter is skipped for those entries.

## Quality Parameters

| Parameter | Default |
|-----------|---------|
| Minimum views | 10,000 |
| Minimum likes/dislikes ratio | 100 |
| Ranking score | `(likes / max(dislikes,1)) × (likes / max(views,1))` |
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: update README for ytscraper — new invocation, Python 3.11+, API note"
```

---

## Task 8: Final verification

- [ ] **Step 1: Run full test suite one last time**

```bash
pytest -v
```

Expected: all tests pass, 0 failures.

- [ ] **Step 2: Verify package structure**

```bash
python -c "
from ytscraper.models import VideoRef, VideoMetadata, ScoredVideo
from ytscraper.search import search
from ytscraper.metadata import fetch
from ytscraper.ranking import filter_and_rank
from ytscraper.cli import main
print('All imports OK')
"
```

Expected: `All imports OK`

- [ ] **Step 3: Verify __main__ entry point works**

```bash
python -m ytscraper --help
```

Expected: usage printed without error.

- [ ] **Step 4: Verify .python-version is present**

```bash
cat .python-version
```

Expected: `3.11`

- [ ] **Step 5: Final commit if any loose files**

```bash
git status
```

If clean: done. If there are uncommitted changes:

```bash
git add -p
git commit -m "chore: final cleanup"
```
