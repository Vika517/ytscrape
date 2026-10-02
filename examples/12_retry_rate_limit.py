"""Configure retries, client-side rate limiting and debug logging.

Run sync:   python examples/12_retry_rate_limit.py
Run async:  python examples/12_retry_rate_limit.py --async
"""

from __future__ import annotations

import argparse
import asyncio
import logging

from ytscrape import (
    AsyncYouTube,
    BotDetected,
    RateLimited,
    RetryPolicy,
    YouTube,
    YtScrapeError,
)

RETRY = RetryPolicy(max_retries=5, backoff_factor=1.0, max_backoff=20.0)


def run_sync() -> None:
    try:
        with YouTube(retry=RETRY, min_interval=1.0) as yt:
            for query in ("python", "rust", "go"):
                video = next(iter(yt.search(query, max_results=1)))
                print(f"{query}: {video.title}")
    except RateLimited as exc:
        print(f"Rate limited, retry after {exc.retry_after}s")
    except BotDetected:
        print("YouTube asked for a captcha — slow down or change IP.")
    except YtScrapeError as exc:
        print(f"Failed: {exc}")


async def run_async() -> None:
    async with AsyncYouTube(retry=RETRY, min_interval=1.0) as yt:
        for query in ("python", "rust", "go"):
            results = await yt.search(query, max_results=1)
            async for video in results:
                print(f"{query}: {video.title}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    logging.getLogger("ytscrape").setLevel(logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument("--async", dest="use_async", action="store_true")
    if parser.parse_args().use_async:
        asyncio.run(run_async())
    else:
        run_sync()
