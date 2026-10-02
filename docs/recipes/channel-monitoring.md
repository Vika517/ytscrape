---
description: Monitor a YouTube channel for new uploads with Python — poll channel_videos() and store seen video ids.
---

# Recipe: channel monitoring

Poll a channel's newest uploads and report the ones you have not seen yet.

=== "Sync"

    ```python
    import json
    import pathlib
    from ytscrape import YouTube

    STATE = pathlib.Path("seen.json")
    seen = set(json.loads(STATE.read_text())) if STATE.exists() else set()

    with YouTube(min_interval=1.0) as yt:
        for video in yt.channel_videos("@GoogleDevelopers", max_results=30):
            if video.video_id not in seen:
                print("NEW:", video.title, video.url, video.published_at)
                seen.add(video.video_id)

    STATE.write_text(json.dumps(sorted(seen)))
    ```

=== "Async"

    ```python
    import asyncio
    from ytscrape import AsyncYouTube

    CHANNELS = ["@GoogleDevelopers", "@PythonSoftwareFoundation"]

    async def latest(yt, channel):
        videos = await yt.channel_videos(channel, max_results=5)
        return [v async for v in videos]

    async def main():
        async with AsyncYouTube(min_interval=0.5) as yt:
            for channel, videos in zip(CHANNELS, await asyncio.gather(*(latest(yt, c) for c in CHANNELS))):
                print(channel, [v.title for v in videos])

    asyncio.run(main())
    ```

Run it from cron or a scheduled GitHub Action.
