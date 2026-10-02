---
description: List all uploads of a YouTube channel in Python with ytscrape's channel_videos() — lazy pagination, no API key.
---

# Channel videos

`channel_videos()` lists a channel's uploads (the **Videos** tab) as a lazy,
paginated iterable (`ChannelVideos` / `AsyncChannelVideos`). Pages are only
fetched as you iterate.

=== "Sync"

    ```python
    from ytscrape import YouTube

    with YouTube() as yt:
        for video in yt.channel_videos("@GoogleDevelopers", max_results=50):
            print(video.title, video.views, video.published_at)
    ```

=== "Async"

    ```python
    from ytscrape import AsyncYouTube

    async with AsyncYouTube() as yt:
        videos = await yt.channel_videos("@GoogleDevelopers", max_results=50)
        async for video in videos:
            print(video.title, video.views)
    ```

`channel` accepts a channel id (`UC...`), an `@handle` or a channel URL.
Omit `max_results` to walk the full upload history.

You can also start from a model: `channel.videos()` or
`channel_details.videos()` (see [Models & navigation](models.md)).

!!! note
    Shorts, live streams, and items rendered as `lockupViewModel` are skipped;
    only regular uploads are yielded as `Video` objects.
