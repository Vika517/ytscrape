---
description: ytscrape exception hierarchy — catch RateLimited, BotDetected, VideoUnavailable, AgeRestricted, ParseError and transcript errors when you scrape YouTube with Python.
---

# Handle ytscrape errors: exceptions and error hierarchy

> Understand the ytscrape exception hierarchy and learn which exception to catch for network errors, rate limits, bot checks, unavailable videos, parse failures, and missing transcripts.

Every error raised by ytscrape derives from a single base class, `YtScrapeError` (`YtScraperError` is kept as an alias), so you always have a clean catch-all.

## Exception hierarchy

```text
YtScrapeError (alias YtScraperError)
├── ContextExtractionError
├── RequestError(status_code, url)
│   ├── RateLimited(retry_after)
│   ├── BotDetected (alias CaptchaRequired)
│   └── ConsentRequired
├── VideoUnavailable(video_id, reason)
│   └── AgeRestricted
├── ParseError
└── TranscriptError
    ├── TranscriptsDisabled
    └── NoTranscriptFound
```

| Exception                | Raised when |
| ------------------------ | ----------- |
| `ContextExtractionError` | The InnerTube context could not be extracted from the YouTube home page. |
| `RequestError`           | An HTTP request failed (network error, timeout, non-2xx) after retries. Has `status_code` and `url`. |
| `RateLimited`            | HTTP 429 persisted after retries; `retry_after` holds the server hint (seconds) if any. |
| `BotDetected`            | YouTube served a captcha / "confirm you're not a bot" page. |
| `ConsentRequired`        | YouTube redirected to the cookie-consent wall. |
| `VideoUnavailable`       | `video()` targets a private, removed or otherwise unplayable video; has `video_id` and `reason`. |
| `AgeRestricted`          | The video requires sign-in for age verification. |
| `ParseError`             | A response could not be parsed (unrecognised structure, invalid id, disabled comments). |
| `TranscriptsDisabled`    | The video has no caption tracks. |
| `NoTranscriptFound`      | Caption tracks exist, but none match the requested languages. |

!!! tip
    Transient failures (429, 5xx, connection errors) are retried automatically —
    see [Reliability](reliability.md).

=== "Sync"

    ```python
    from ytscrape import AgeRestricted, BotDetected, RateLimited, VideoUnavailable, YouTube, YtScrapeError

    with YouTube() as yt:
        try:
            details = yt.video("dQw4w9WgXcQ")
        except AgeRestricted:
            print("Age-restricted")
        except VideoUnavailable as exc:
            print(f"Unavailable: {exc.reason}")
        except RateLimited as exc:
            print(f"Slow down, retry after {exc.retry_after}s")
        except BotDetected:
            print("Bot check — change IP or wait")
        except YtScrapeError as exc:
            print(f"Other error: {exc}")
    ```

=== "Async"

    ```python
    from ytscrape import AsyncYouTube, VideoUnavailable, YtScrapeError

    async with AsyncYouTube() as yt:
        try:
            details = await yt.video("dQw4w9WgXcQ")
        except VideoUnavailable as exc:
            print(f"Unavailable: {exc.reason}")
        except YtScrapeError as exc:
            print(f"Other error: {exc}")
    ```

## Code example

```python
from ytscrape import (
    YouTube,
    YtScraperError,
    RequestError,
    ParseError,
)


def main() -> None:
    with YouTube() as yt:
        # An invalid id/URL cannot be parsed into a video id.
        try:
            yt.video("not-a-real-video-id")
        except ParseError as exc:
            print(f"Could not parse video id: {exc}")

        # Network / HTTP failures surface as RequestError.
        try:
            details = yt.video("dQw4w9WgXcQ")
            print(f"Got: {details.title}")
        except RequestError as exc:
            print(f"Request to YouTube failed: {exc}")
        except YtScraperError as exc:
            # Catch-all for any other ytscrape error.
            print(f"Something went wrong: {exc}")


if __name__ == "__main__":
    main()
```

## Transcript exceptions in detail

The two transcript-specific exceptions carry extra context that helps you react appropriately.

### `NoTranscriptFound`

Raised when `yt.transcript()` or `TranscriptList.find_transcript()` cannot match any of the requested language codes to an available track.

| Attribute   | Type              | Description                                     |
| ----------- | ----------------- | ----------------------------------------------- |
| `video_id`  | `str`             | The video that was queried.                     |
| `requested` | `tuple[str, ...]` | The language codes that were requested.         |
| `available` | `tuple[str, ...]` | The language codes that are actually available. |

```python
from ytscrape import YouTube, NoTranscriptFound

with YouTube() as yt:
    try:
        transcript = yt.transcript("dQw4w9WgXcQ", languages=["zh", "ar"])
    except NoTranscriptFound as exc:
        print(f"Requested: {list(exc.requested)}")
        print(f"Available: {list(exc.available)}")
```

### `TranscriptsDisabled`

Raised when a video has no caption tracks at all.

| Attribute  | Type  | Description                            |
| ---------- | ----- | -------------------------------------- |
| `video_id` | `str` | The video whose captions are disabled. |

```python
from ytscrape import YouTube, TranscriptsDisabled

with YouTube() as yt:
    try:
        transcript = yt.transcript("VIDEO_WITHOUT_CAPTIONS")
    except TranscriptsDisabled as exc:
        print(f"Captions are disabled for: {exc.video_id}")
```

## When to catch each exception

| Goal                                                | Exception to catch       |
| --------------------------------------------------- | ------------------------ |
| Any network or HTTP problem                         | `RequestError`           |
| Bad input, disabled comments, unrecognised response | `ParseError`             |
| YouTube home page unreachable at startup            | `ContextExtractionError` |
| No captions at all on the video                     | `TranscriptsDisabled`    |
| Captions exist but not in the requested language    | `NoTranscriptFound`      |
| Any caption-related failure                         | `TranscriptError`        |
| Any ytscrape failure                                | `YtScraperError`         |

!!! tip

    Catching `YtScraperError` at the outermost level is the simplest guard when you don't need to distinguish the failure mode — for example in a CLI tool or a background worker that just logs the error and moves on.


!!! note "Bot checks and blocks"

    Some `ParseError` / `ContextExtractionError` messages indicate a consent wall, captcha, or bot check (including transcript PO-token / `exp=xpe` failures). The message recommends changing your IP or using a proxy (that helps in most cases); if it still fails, open a [GitHub issue](https://github.com/vsmutok/ytscrape/issues). The same exceptions apply under `AsyncYouTube`.
