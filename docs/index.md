---
description: ytscrape is a free YouTube scraper for Python — search, video and channel metadata, scrape YouTube comments, fetch YouTube transcripts in Python and list channel uploads. Works without a YouTube API key.
---

<p align="center">
  <img class="ytscrape-wordmark" src="assets/logo_text_dark.png" alt="ytscrape" width="520">
</p>

# ytscrape — Free Open-Source Python YouTube Scraper

**Scrape YouTube from Python without an API key.** Search, video and channel
metadata, comments and replies, transcripts and channel uploads — plain HTTP,
typed models, sync *and* async.

[Get started](quickstart.md){ .md-button .md-button--primary }
[Examples](examples.md){ .md-button }
[What's new in 2.0](migration-2.0.md){ .md-button }

ytscrape talks directly to YouTube's internal *InnerTube* API (the same endpoints the YouTube web app uses), parses responses into frozen, fully-typed dataclasses, and paginates for you.

## Features

<div class="grid cards" markdown>

-   :material-key-remove:{ .lg .middle } **YouTube API without a key**

    ---

    No Google Cloud project, no credentials, no daily quota.

-   :material-magnify:{ .lg .middle } **Search**

    ---

    Videos, channels, playlists, Shorts and movies with `SearchFilter`. [Guide](guides/searching.md)

-   :material-information-outline:{ .lg .middle } **Video & channel metadata**

    ---

    Numeric views and subscribers, datetimes, thumbnails. [Models](guides/models.md)

-   :material-comment-multiple-outline:{ .lg .middle } **Scrape YouTube comments**

    ---

    Every comment and reply with `yt.comments()`. [Guide](guides/comments.md)

-   :material-subtitles-outline:{ .lg .middle } **YouTube transcripts in Python**

    ---

    Manual or auto-generated captions, any language. [Guide](guides/transcripts.md)

-   :material-playlist-play:{ .lg .middle } **Channel uploads**

    ---

    Lazy `channel_videos()` over the Videos tab. [Guide](guides/channel-videos.md)

-   :material-shield-refresh-outline:{ .lg .middle } **Reliable**

    ---

    Retries with backoff, rate limiting, bot/consent detection. [Guide](guides/reliability.md)

-   :material-lightning-bolt-outline:{ .lg .middle } **Async API**

    ---

    `AsyncYouTube` on httpx with concurrency limits. [Guide](guides/async.md)

</div>

## Quick example

```bash
pip install ytscrape
```

=== "Sync"

    ```python
    from ytscrape import SearchFilter, YouTube

    with YouTube() as yt:
        for video in yt.search("python tutorial", filter=SearchFilter.VIDEOS, max_results=5):
            print(video.title, video.views, video.url)

        transcript = yt.transcript("dQw4w9WgXcQ", languages=["en"])
        print(transcript.text[:200])

        for comment in yt.comments("dQw4w9WgXcQ", max_results=10):
            print(comment.author, comment.like_count, comment.text)
    ```

=== "Async"

    ```python
    import asyncio
    from ytscrape import AsyncYouTube

    async def main() -> None:
        async with AsyncYouTube() as yt:
            results = await yt.search("python tutorial", max_results=5)
            async for video in results:
                details = await video.details()
                print(details.title, details.views, details.published_at)

    asyncio.run(main())
    ```

## How ytscrape Compares

|                         | **ytscrape** | YouTube Data API | `yt-dlp` | Browser automation |
| ----------------------- | :----------: | :--------------: | :------: | :----------------: |
| API key required        |       ❌      |         ✅        |     ❌    |          ❌         |
| Daily quota             |       ❌      |         ✅        |     ❌    |          ❌         |
| Browser / driver needed |       ❌      |         ❌        |     ❌    |          ✅         |
| Search                  |       ✅      |         ✅        |     ✅    |          ✅         |
| Video metadata          |       ✅      |         ✅        |     ✅    |          ✅         |
| Comments + replies      |       ✅      |     ✅ (quota)    |     ✅    |          ✅         |
| Typed Python models     |       ✅      |         ❌        |     ❌    |          ❌         |
| Async (`asyncio`) API   |       ✅      |         ❌        |     ❌    |        varies      |
| Downloads media         |       ❌      |         ❌        |     ✅    |          ✅         |
| Install size            |     tiny     |      medium      |   large  |        huge        |

**Rule of thumb:** use `yt-dlp` when you need to download media, the official Data API when you need guaranteed, ToS-blessed access, and ytscrape when you need **fast, key-less access to YouTube metadata and comments** from Python.

## How It Works

ytscrape speaks YouTube's private *InnerTube* API directly, with no browser in the loop:

1. **Context extraction.** On first use, ytscrape fetches `youtube.com` once and extracts the InnerTube context — the API key, client version, and visitor data — embedded in the page's initial JavaScript.

2. **POST requests.** Every subsequent call POSTs to one of YouTube's internal JSON endpoints — `youtubei/v1/search`, `youtubei/v1/player`, `youtubei/v1/browse`, or `youtubei/v1/next` — with that context attached as the request body.

3. **Typed parsing.** Responses are parsed from deeply-nested JSON into small, frozen dataclasses (`Video`, `Channel`, `VideoDetails`, `Comment`, etc.) with full type hints. The package ships `py.typed`, so mypy and pyright see every field.

4. **Transparent pagination.** Continuation tokens returned by YouTube are stored internally. Iterating the result object automatically fires the next page request whenever you exhaust the current batch — you never handle tokens manually.

!!! note

    ytscrape accesses YouTube's private, undocumented endpoints. The API contracts and internal `params` values may change without notice. Use this library responsibly, respect YouTube's Terms of Service, and avoid aggressive request rates. It is provided for research and educational purposes — you are responsible for your usage.


## Next Steps

Ready to make your first request? Head to the [Quickstart](quickstart.md) to install ytscrape and run your first search in under five minutes. Prefer copy-paste scripts? See [Examples](examples.md) (every feature has sync + async). For concurrent scraping, read the [Async API guide](guides/async.md).
