---
description: Make your Python YouTube scraper robust — automatic retries with backoff, Retry-After support, client-side rate limiting, context caching, logging and bot detection in ytscrape.
---

# Reliability: retries, rate limits and caching

YouTube occasionally answers with `429 Too Many Requests`, `5xx` errors, or a
captcha/consent page. ytscrape 2.0 ships with built-in tools to handle this.

## Retries with `RetryPolicy`

Every client retries transient failures by default with exponential backoff:

```python
RetryPolicy(
    max_retries=3,
    backoff_factor=0.5,       # delay = backoff_factor * 2**attempt
    max_backoff=30.0,         # upper bound for a single delay (seconds)
    jitter=True,              # randomise delays to avoid thundering herds
    retry_statuses={408, 425, 429, 500, 502, 503, 504},
    retry_on_connection_errors=True,
    respect_retry_after=True, # honour the Retry-After header
)
```

=== "Sync"

    ```python
    from ytscrape import RetryPolicy, YouTube

    with YouTube(retry=RetryPolicy(max_retries=5, backoff_factor=1.0)) as yt:
        details = yt.video("dQw4w9WgXcQ")
    ```

=== "Async"

    ```python
    from ytscrape import AsyncYouTube, RetryPolicy

    async with AsyncYouTube(retry=RetryPolicy(max_retries=5)) as yt:
        details = await yt.video("dQw4w9WgXcQ")
    ```

Disable retries completely with `RetryPolicy.disabled()`. Use
`policy.compute_delay(attempt, retry_after=None)` to preview a delay.

## Client-side rate limiting

`RateLimiter(min_interval=...)` enforces a minimum gap between requests
(`.wait()` for sync, `.async_wait()` for async). The shortcut
`min_interval=` creates one for you:

=== "Sync"

    ```python
    from ytscrape import RateLimiter, YouTube

    limiter = RateLimiter(min_interval=1.0)   # max ~1 request / second
    with YouTube(rate_limiter=limiter) as yt:
        ...
    # or simply: YouTube(min_interval=1.0)
    ```

=== "Async"

    ```python
    from ytscrape import AsyncYouTube

    async with AsyncYouTube(min_interval=1.0) as yt:
        ...
    ```

A single `RateLimiter` can be shared between several clients.

## Context caching

Each client bootstraps an InnerTube context (API key, client version) from the
YouTube homepage. `ContextCache(ttl=3600)` stores it so repeated clients skip
this request. `ytscrape.context.DEFAULT_CONTEXT_CACHE` is a process-wide cache
keyed by `(language, region)`.

| `context_cache=` | Behaviour |
| ---------------- | --------- |
| `None` (default) | Use the global cache only when the client owns its HTTP session |
| `True` | Always use the global cache |
| `False` | Never cache |
| `ContextCache(...)` | Use your own instance |

```python
from ytscrape import ContextCache, YouTube

cache = ContextCache(ttl=600)
with YouTube(context_cache=cache) as yt:
    ...
cache.invalidate()   # drop everything (or pass a key)
```

## Block detection

ytscrape recognises common blocking responses and raises specific exceptions
(all subclasses of `RequestError`):

- `RateLimited` — HTTP 429 after retries; `retry_after` holds the hint in seconds.
- `BotDetected` (alias `CaptchaRequired`) — "Sign in to confirm you're not a bot" / captcha.
- `ConsentRequired` — EU cookie-consent wall.

See [Error handling](error-handling.md).

## Logging

All requests, retries and timings are logged at `DEBUG` level on the
`ytscrape` logger:

```python
import logging

logging.basicConfig(level=logging.INFO)
logging.getLogger("ytscrape").setLevel(logging.DEBUG)
```

!!! tip
    For large jobs, combine `min_interval`, a generous `RetryPolicy`, and
    `max_concurrency` (async) rather than hammering YouTube.
