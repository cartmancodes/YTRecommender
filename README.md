# YTscraper

Fetch and rank YouTube videos by quality — filtered by views and like/dislike ratio, sorted by a quality score.

**Requires Python 3.11+**

> Dislike counts are sourced from the [Return YouTube Dislike API](https://returnyoutubedislikeapi.com/), a community-maintained service. They are estimates, not the original YouTube counts (YouTube removed public dislike counts in November 2021).

## Setup

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

> **Optional — suppress yt-dlp JS runtime warnings:** yt-dlp will warn that no JavaScript runtime is installed. The scraper works without one, but to silence the warning install [Deno](https://deno.com/):
> ```bash
> brew install deno   # macOS
> # or: curl -fsSL https://deno.land/install.sh | sh
> ```

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
python -m ytscraper -c "chill indie playlist" -p 5 --top 5
```

```
 #  Score   Views    Likes   Dislikes  Title                               URL
 1  3.052   5.6M     135K    1K        late night vibes | escape reality p https://www.youtube.com/watch?v=ObVsY50NMkQ
 2  2.579   1.5M     30K     219       everything is going to be alright [ https://www.youtube.com/watch?v=tastBJdz8KY
```

A `*` after the Dislikes value means the Return YouTube Dislike API was unavailable for that video; the like/dislike ratio filter is skipped for those entries.

## JSON output

```bash
python -m ytscraper -c "chill indie playlist" -p 5 --top 3 --json
```

```json
[
  {
    "url": "https://www.youtube.com/watch?v=ObVsY50NMkQ",
    "title": "late night vibes | escape reality playlist",
    "views": 5600000,
    "likes": 135000,
    "dislikes": 1000,
    "dislikes_available": true,
    "score": 3.0518
  }
]
```

## Quality Parameters

| Parameter | Default |
|-----------|---------|
| Minimum views | 10,000 |
| Minimum likes/dislikes ratio | 100 |
| Ranking score | `(likes / max(dislikes,1)) × (likes / max(views,1))` |
