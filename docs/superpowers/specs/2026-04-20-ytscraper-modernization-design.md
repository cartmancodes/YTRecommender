# YTscraper Modernization — Design

**Date:** 2026-04-20
**Status:** Approved for planning

## 1. Goal & Scope

Revive YTscraper so it works against modern YouTube and delivers a **ranked** list of "interested" videos for a given search query. Replace broken HTML-scraping with `yt-dlp` for search and metadata, use the Return YouTube Dislike API to recover dislike counts (public dislike counts were removed by YouTube in November 2021), rename the package to comply with PEP 8, and declare a Python 3.11+ floor.

**In scope**
- Replace search backend (`youtube-search-python`) with `yt-dlp`.
- Replace HTML scraping (`requests-html` + `pyppeteer` + `BeautifulSoup`) with `yt-dlp` metadata extraction.
- Add Return YouTube Dislike API integration for dislikes.
- Rank filtered results by a quality score and print a table (or JSON) of top videos.
- Rename `YTlib/` → `ytscraper/`; fix broken module imports.
- Declare Python floor via `.python-version` and README.
- Replace `optparse` with `argparse`.
- Slim `requirements.txt` to current, actively maintained dependencies.
- Unit tests for ranking and metadata logic.

**Out of scope**
- Web/GUI interface.
- Persistent storage / database.
- YouTube Data API v3 integration (considered and rejected in favor of `yt-dlp`, no API key required).
- Multi-platform support (TikTok, Vimeo, etc.).
- `pyproject.toml` migration (user elected to keep `requirements.txt`).
- Retry / backoff logic for flaky APIs (v1 degrades gracefully instead).
- Integration tests against live YouTube.

## 2. Architecture

Four modules inside a renamed `ytscraper/` package, each with a single responsibility and a well-defined interface. Data flows in one direction: `cli → search → metadata → ranking → cli`.

```
ytscraper/
├── __init__.py
├── cli.py          # entry point — argparse + orchestration + output
├── search.py       # query → list[VideoRef]
├── metadata.py     # list[VideoRef] → list[VideoMetadata]
├── ranking.py      # list[VideoMetadata] → list[ScoredVideo]
└── models.py       # shared dataclasses: VideoRef, VideoMetadata, ScoredVideo
```

### Module Contracts

**`search.py`**
- `search(query: str, limit: int) -> list[VideoRef]`
- Wraps `yt-dlp`'s `ytsearch{N}:{query}` extractor with `extract_flat=True` (fast; no per-video page fetch).
- Returns lightweight refs containing video id, canonical url, and title.

**`metadata.py`**
- `fetch(refs: list[VideoRef]) -> list[VideoMetadata]`
- For each ref, concurrently (via `concurrent.futures.ThreadPoolExecutor`, since `yt-dlp` is blocking):
  1. Calls `yt-dlp` with the video URL to get `view_count`, `like_count`, `channel`, `duration`, `title`.
  2. Calls Return YouTube Dislike API (`https://returnyoutubedislikeapi.com/votes?videoId={id}`) via `httpx` to get `dislikes`.
- Videos where `yt-dlp` metadata extraction fails are **excluded** (logged to stderr).
- Videos where the dislike API fails are **kept**, with `dislikes = 0` and `dislikes_available = False`; ranking degrades to pure engagement score.

**`ranking.py`**
- `filter_and_rank(videos: list[VideoMetadata], min_views: int, min_like_ratio: float) -> list[ScoredVideo]`
- Applies hard-floor filters: `views >= min_views` AND (`dislikes == 0` OR `likes / dislikes >= min_like_ratio`).
- When `dislikes_available is False`, the like-ratio filter is skipped for that video (we have no dislike data to filter against).
- Sorts descending by quality score: `score = (likes / max(dislikes, 1)) * (likes / max(views, 1))`.
- Pure function — no IO, fully unit-testable.

**`cli.py`**
- Parses flags with `argparse`, wires the pipeline, formats output.
- Default output: ranked table. With `--json`: pipe-friendly JSON.
- Entry point: `python -m ytscraper ...` (no console script installed, consistent with no-`pyproject.toml` decision).

### Data Flow

```
cli.py
  ↓  query, limit
search.py — yt-dlp ytsearchN:
  ↓  list[VideoRef]
metadata.py — yt-dlp per video (parallel) + Return YouTube Dislike API
  ↓  list[VideoMetadata]
ranking.py — filter + sort (pure)
  ↓  list[ScoredVideo]
cli.py — table or JSON to stdout
```

No module imports from any other module's internals; all communication is through the dataclasses in `models.py`.

## 3. CLI & Output

### Invocation

```
python -m ytscraper -c "chill indie playlist" -p 20 --min-views 10000 --min-like-ratio 100 --top 10
```

### Flags

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `-c`, `--content` | yes | — | Search query. |
| `-p`, `--pages` | no | 10 | Number of search candidates to fetch. Kept as `-p` for README back-compat; internally represents `limit`. |
| `--min-views` | no | 10000 | Minimum views to include a video. |
| `--min-like-ratio` | no | 100 | Minimum likes-to-dislikes ratio (applied only when dislikes data is real). |
| `--top` | no | all passing | Number of ranked results to print. |
| `--json` | no | off | Emit JSON array instead of the default table. |

### Default output (table)

```
 #  Score   Views    Likes   Dislikes  Title                           URL
 1  0.421   1.2M     95K     210       Best Chill Indie 2025           https://youtu.be/AAA
 2  0.318   480K     38K     95        Late Night Indie Mix            https://youtu.be/BBB
```

- `Score` is the ranking score (higher = better).
- Counts use human-readable formatting (`1.2M`, `480K`).
- A trailing asterisk on `Dislikes` indicates `dislikes_available = False` (API failure fallback).

### JSON output

```json
[
  {
    "url": "https://youtu.be/AAA",
    "title": "Best Chill Indie 2025",
    "views": 1200000,
    "likes": 95000,
    "dislikes": 210,
    "dislikes_available": true,
    "score": 0.4211
  }
]
```

### Logging

- Per-video extraction failures go to `stderr`, do not appear in stdout.
- `stdout` is reserved for the ranked output so JSON mode is pipe-clean.

## 4. Python Version & Dependencies

### Python floor

- `>= 3.11` — declared by:
  - `.python-version` file at repo root containing `3.11`.
  - Note in `README.md`: "Requires Python 3.11+".

### New `requirements.txt`

```
yt-dlp
httpx
pytest
```

No version pins beyond what's strictly needed — consistent with the original file's style and user's "keep requirements.txt" direction. `pytest` is development-only but included for simplicity of a single requirements file (no separate `requirements-dev.txt`).

### Removed

`anyio`, `appdirs`, `beautifulsoup4`, `bs4`, `certifi`, `chardet`, `cssselect`, `fake-useragent`, `h11`, `httpcore`, `idna`, `lxml`, `parse`, `pyee`, `pyppeteer`, `pyquery`, `requests`, `requests-html`, `rfc3986`, `six`, `sniffio`, `soupsieve`, `tqdm`, `urllib3`, `w3lib`, `websockets`, `youtube-search-python`.

## 5. Error Handling

Per project conventions: validate only at system boundaries, no speculative try/except.

| Failure | Behavior |
|---------|----------|
| `yt-dlp` search returns empty list | Print "No results" to stderr, exit code 1. |
| `yt-dlp` metadata fetch fails for a single video | Log to stderr with url + error summary, exclude from results. |
| Return YouTube Dislike API 4xx / 5xx / timeout / network error | Set `dislikes = 0`, `dislikes_available = False`; video is kept but bypasses the like-ratio floor filter. |
| All videos failed metadata extraction | Print "No metadata extractable" to stderr, exit code 1. |
| Invalid CLI arguments | `argparse` handles via its built-in usage/error behavior. |

No retry or backoff logic in v1. If the dislike API proves flaky in practice, revisit.

## 6. Testing

Unit tests under `tests/`:

- **`test_ranking.py`** — pure-function tests for `filter_and_rank`:
  - Filters videos below `min_views`.
  - Filters videos below `min_like_ratio` (when dislikes are real).
  - Skips like-ratio filter when `dislikes_available = False`.
  - Sorts by score descending.
  - Handles `dislikes = 0` without ZeroDivisionError.
- **`test_metadata.py`** — `metadata.fetch`:
  - `yt-dlp` monkey-patched to return a canned `info_dict`.
  - Return YouTube Dislike API mocked via `respx` or `httpx.MockTransport`.
  - Success case populates `VideoMetadata` fully.
  - Dislike API failure falls back to `dislikes=0, dislikes_estimated=False`.
  - Dislike API failure for one video still preserves the other videos' full metadata.
- **`test_cli.py`** — smoke test: invoke `python -m ytscraper` via `subprocess` with the pipeline mocked at module level, assert table and JSON formats render correctly.

No integration tests against live YouTube — they are slow, flaky, and not gate-keepable in CI.

## 7. Migration Notes

- `YTlib/` is removed entirely. The previous `content_getter.py`, `content_scraper.py`, `get_content.py`, `utils.py` have no business logic worth preserving beyond the filter constants (`MIN_VIEWS=10000`, `LIKE_FACTOR=100`) which become CLI defaults.
- README is updated with:
  - New invocation (`python -m ytscraper ...`).
  - Python version requirement.
  - Note that the dislike count is sourced from Return YouTube Dislike API, not YouTube directly.

## 8. Open Questions

None at design time. Questions that came up during brainstorming and were resolved:

1. Dislike count source → Return YouTube Dislike API.
2. Python floor → `>= 3.11`.
3. Search + metadata backend → `yt-dlp`.
4. Output shape → filter + rank + table/JSON.
5. Packaging → keep `requirements.txt`, no `pyproject.toml`.
6. Module layout → rename `YTlib/` → `ytscraper/`.
