---
description: Frequently asked questions about ytscrape — scraping YouTube without an API key, legality, rate limits, bot detection, and comparison with yt-dlp and the YouTube Data API.
---

# FAQ

??? question "Do I need a YouTube API key?"
    No. ytscrape talks to YouTube's internal InnerTube API — the same endpoints
    the website uses — so there is no key, no Google Cloud project, and no quota.

??? question "How is this different from yt-dlp?"
    yt-dlp focuses on downloading media. ytscrape focuses on **data**: search,
    metadata, comments, transcripts and channel uploads, returned as typed
    Python objects, with a sync and an async API.

??? question "I get `RateLimited` or `BotDetected`. What now?"
    Slow down: use `min_interval=`, a larger `RetryPolicy`, and lower
    concurrency. A different IP/proxy can help too. See [Reliability](guides/reliability.md).

??? question "Why is `published_at` approximate?"
    Search results only show relative text like "3 weeks ago". Use
    `video.details().published_at` for the exact date.

??? question "Why is `views` `None`?"
    YouTube did not show a count (e.g. upcoming premieres). The raw wording is in `views_text`.

??? question "Is scraping YouTube legal?"
    Check YouTube's Terms of Service and the laws in your jurisdiction. Only
    collect public data, respect rate limits, and do not redistribute content.

??? question "Does it work with asyncio?"
    Yes — install `ytscrape[async]` and use `AsyncYouTube`. See [Async API](guides/async.md).

??? question "Something broke after a YouTube change."
    Open an issue with the failing call and, if possible, the debug log of the
    `ytscrape` logger.
