# YTscraper

> Fetch and rank YouTube videos by quality — filtered by views and like/dislike ratio, sorted by a composite quality score.

**Requires Python 3.11+**

---

## How it works

1. Searches YouTube for candidate videos using [`yt-dlp`](https://github.com/yt-dlp/yt-dlp)
2. Fetches per-video metadata (views, likes) concurrently via `yt-dlp`
3. Fetches dislike counts from the [Return YouTube Dislike API](https://returnyoutubedislikeapi.com/) *(YouTube removed public dislike counts in November 2021)*
4. Filters by minimum views and like/dislike ratio
5. Ranks by quality score: `(likes / max(dislikes, 1)) × (likes / max(views, 1))`

---

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows

pip install -e .                 # installs ytscraper as a shell command
pip install -e ".[dev]"          # also installs pytest
```

---

## Usage

```bash
ytscraper -c "<search query>" [options]
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `-c`, `--content` | **required** | Search query |
| `-p`, `--pages` | `10` | Number of candidate videos to fetch from search |
| `--min-views` | `10000` | Minimum view count to include a video |
| `--min-like-ratio` | `100` | Minimum likes-to-dislikes ratio (skipped if dislikes unavailable) |
| `--top` | all | Limit the number of results shown |
| `--json` | off | Output results as a JSON array instead of a table |
| `-h`, `--help` | | Show help and exit |

---

## Examples

### Basic search

```bash
ytscraper -c "chill indie playlist" -p 20
```

### Limit results

```bash
ytscraper -c "lo-fi beats" -p 15 --top 5
```

```
 #  Score   Views    Likes   Dislikes  Title                               URL
 1  1.873   54.1M    484K    2K        Best of lofi hip hop 2021 ✨ [beats  https://www.youtube.com/watch?v=n61ULEU7CO0
 2  1.599   132.2M   2.1M    21K       1 A.M Study Session 📚 [lofi hip hop https://www.youtube.com/watch?v=lTRiuFIWV54
 3  1.243   643.2M   3.5M    15K       lofi hip hop radio 📚 beats to relax https://www.youtube.com/watch?v=jfKfPfyJRdk
```

> A `*` after the Dislikes count means the Return YouTube Dislike API was unavailable for that video; the like/dislike ratio filter is skipped for those entries.

### Custom quality thresholds

```bash
ytscraper -c "jazz piano" -p 20 --min-views 50000 --min-like-ratio 200 --top 10
```

### JSON output (for scripting)

```bash
ytscraper -c "lo-fi beats" -p 5 --top 2 --json
```

```json
[
  {
    "url": "https://www.youtube.com/watch?v=n61ULEU7CO0",
    "title": "Best of lofi hip hop 2021 ✨ [beats to relax/study to]",
    "views": 54125467,
    "likes": 483772,
    "dislikes": 2308,
    "dislikes_available": true,
    "score": 1.8735
  },
  {
    "url": "https://www.youtube.com/watch?v=lTRiuFIWV54",
    "title": "1 A.M Study Session 📚 [lofi hip hop]",
    "views": 132205507,
    "likes": 2111252,
    "dislikes": 21082,
    "dislikes_available": true,
    "score": 1.5993
  }
]
```

---

## Quality scoring

| Parameter | Default | Description |
|-----------|---------|-------------|
| Minimum views | 10,000 | Hard floor — videos below this are excluded |
| Minimum like/dislike ratio | 100 | Hard floor — excluded when `likes / dislikes < ratio` |
| Ranking score | `(likes / max(dislikes,1)) × (likes / max(views,1))` | Higher is better |

The score rewards videos that are both well-liked relative to dislikes *and* have strong engagement relative to total views.

---

## Running tests

```bash
pip install -e ".[dev]"     # installs pytest via pyproject.toml dev extras
python -m pytest -v
```

---

## Project structure

```
ytscraper/
├── __init__.py
├── __main__.py      # ytscraper entry point
├── cli.py           # argument parsing + output formatting
├── search.py        # yt-dlp search wrapper
├── metadata.py      # concurrent metadata + dislike API fetch
├── ranking.py       # filter and rank by quality score
└── models.py        # VideoRef, VideoMetadata, ScoredVideo dataclasses

tests/
├── test_models.py
├── test_ranking.py
├── test_search.py
├── test_metadata.py
└── test_cli.py
```
