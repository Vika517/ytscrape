"""Navigate between models: search result -> details -> channel -> uploads.

Run sync:   python examples/13_navigation_helpers.py
Run async:  python examples/13_navigation_helpers.py --async
"""

from __future__ import annotations

import argparse
import asyncio

from ytscrape import AsyncYouTube, SearchFilter, YouTube


def run_sync() -> None:
    with YouTube() as yt:
        video = next(iter(yt.search("lofi hip hop", filter=SearchFilter.VIDEOS)))
        details = video.details()
        print(
            f"{details.title} — {details.views} views, uploaded {details.uploaded_at}"
        )
        for comment in video.comments(max_results=3):
            print(f"  💬 {(comment.text or '')[:70]}")
        channel = video.channel_details()
        print(f"Channel: {channel.title} ({channel.subscribers} subscribers)")
        for upload in channel.videos(max_results=5):
            print(f"  ▶ {upload.title}")


async def run_async() -> None:
    async with AsyncYouTube() as yt:
        results = await yt.search("lofi hip hop", filter=SearchFilter.VIDEOS)
        async for video in results:
            details = await video.details()
            print(f"{details.title} — {details.views} views")
            channel = await video.channel_details()
            uploads = await channel.videos(max_results=5)
            async for upload in uploads:
                print(f"  ▶ {upload.title}")
            break


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--async", dest="use_async", action="store_true")
    if parser.parse_args().use_async:
        asyncio.run(run_async())
    else:
        run_sync()
