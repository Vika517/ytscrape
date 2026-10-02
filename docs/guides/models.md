---
description: ytscrape data models — numeric view and subscriber counts, published_at datetimes, thumbnails and navigation helpers like video.details(), video.comments() and channel.videos().
---

# Models & navigation

All results are frozen, typed dataclasses. Version 2.0 makes them easier to
analyse and to chain together.

## Numeric fields

Counts are parsed into integers; the original wording is kept in `*_text`.

| Model | Numeric | Raw text |
| ----- | ------- | -------- |
| `Video` | `views` | `views_text` |
| `Channel` | `subscribers`, `video_count` | `subscribers_text`, `video_count_text` |
| `Playlist` | `video_count` | `video_count_text` |
| `ChannelDetails` | `subscribers`, `video_count`, `view_count` | `*_text` |
| `VideoDetails` | `views` | — |

Abbreviations like `1.2M` or `12K` are expanded (`parse_count`). Values are
`None` when YouTube does not show them.

## Dates

- `Video.published_text` — e.g. `"3 days ago"`; `Video.published_at` — an
  approximate UTC `datetime` derived from English relative text (`parse_relative_time`).
  Use `language="en"` for reliable parsing.
- `VideoDetails.published_at` / `uploaded_at` — exact datetimes (`parse_date`).

## Thumbnails

`thumbnails` is a tuple of `Thumbnail(url, width, height)` on `Video`,
`Channel`, `Playlist`, `VideoDetails` and `ChannelDetails`. The `thumbnail`
string (best URL) is kept for convenience.

```python
best = max(video.thumbnails, key=lambda t: (t.width or 0))
```

## Navigation helpers

Models returned by `YouTube` / `AsyncYouTube` are *bound* to the client, so you
can navigate without passing ids around:

| Model | Helpers |
| ----- | ------- |
| `Video` | `.details()`, `.comments(**kw)`, `.channel_details()` |
| `VideoDetails` | `.comments(**kw)`, `.channel_details()` |
| `Channel` | `.details()`, `.videos(**kw)` |
| `ChannelDetails` | `.videos(**kw)` |

=== "Sync"

    ```python
    from ytscrape import YouTube

    with YouTube() as yt:
        video = next(iter(yt.search("python asyncio")))
        details = video.details()
        for comment in video.comments(max_results=5):
            print(comment.text)
        channel = video.channel_details()
        for upload in channel.videos(max_results=10):
            print(upload.title)
    ```

=== "Async"

    ```python
    from ytscrape import AsyncYouTube

    async with AsyncYouTube() as yt:
        results = await yt.search("python asyncio", max_results=1)
        async for video in results:
            details = await video.details()
            channel = await video.channel_details()
            uploads = await channel.videos(max_results=10)
            async for upload in uploads:
                print(upload.title)
    ```

Models you construct yourself (or load from JSON) are unbound; calling a helper
raises `UnboundModelError`. Use `model.bind(yt)` to attach a client.

## Export

`to_dict` / `dump_json` / `dump_csv` serialise datetimes as ISO 8601 strings
and thumbnails as lists of dicts. See [Export](export.md).
