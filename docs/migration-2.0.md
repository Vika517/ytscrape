---
description: Upgrade guide from ytscrape 1.x to 2.0 — numeric counts, published_at, thumbnails, new exceptions and reliability options.
---

# Migrating to 2.0

ytscrape 2.0 contains **breaking model changes**. Most code needs only small edits.

## Counts are integers

| 1.x | 2.0 |
| --- | --- |
| `video.views` → `"1.2M views"` | `video.views` → `1200000`, `video.views_text` → `"1.2M views"` |
| `channel.subscribers` → `"3.4M subscribers"` | `channel.subscribers` → `3400000`, `subscribers_text` |
| `channel.video_count`, `playlist.video_count` (str) | `int \| None` + `video_count_text` |
| `ChannelDetails.subscribers/video_count/view_count` (str) | `int \| None` + `*_text` |

```python
# before
print(video.views)
# after: either the raw text or a formatted int
print(video.views_text)
print(f"{video.views:,}" if video.views is not None else "n/a")
```

## `Video.published` was removed

Use `video.published_text` (raw) or `video.published_at` (approximate UTC
datetime). `VideoDetails` gains `published_at` and `uploaded_at` datetimes.

## Thumbnails

`thumbnails` (tuple of `Thumbnail(url, width, height)`) is new; `thumbnail` remains.

## Exceptions

The base class is now `YtScrapeError` (`YtScraperError` remains an alias).
New subclasses: `RateLimited`, `BotDetected`/`CaptchaRequired`,
`ConsentRequired`, `VideoUnavailable`, `AgeRestricted`. `video()` now raises
`VideoUnavailable`/`AgeRestricted` instead of returning partial data. See
[Error handling](guides/error-handling.md).

## Exports

JSON/CSV exports contain ISO datetimes and thumbnail lists; columns renamed as above.

## New (non-breaking)

- Automatic retries and rate limiting — [Reliability](guides/reliability.md)
- `channel_videos()` — [Channel videos](guides/channel-videos.md)
- Navigation helpers — [Models & navigation](guides/models.md)
