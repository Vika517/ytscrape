"""List a channel's uploads (Videos tab) lazily.

Run sync:   python examples/11_channel_videos.py
Run async:  python examples/11_channel_videos.py --async
"""

from __future__ import annotations

import argparse
import asyncio

from ytscrape import AsyncYouTube, YouTube

CHANNEL = "@GoogleDevelopers"


def run_sync() -> None:
    with YouTube() as yt:
        for video in yt.channel_videos(CHANNEL, max_results=15):
            print(f"{video.title} — {video.views_text} ({video.published_text})")


async def run_async() -> None:
    async with AsyncYouTube() as yt:
        videos = await yt.channel_videos(CHANNEL, max_results=15)
        async for video in videos:
            print(f"{video.title} — {video.views_text} ({video.published_text})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--async", dest="use_async", action="store_true")
    if parser.parse_args().use_async:
        asyncio.run(run_async())
    else:
        run_sync()
