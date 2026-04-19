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
