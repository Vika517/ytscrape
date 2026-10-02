---
description: API reference for ytscrape reliability primitives — RetryPolicy, RateLimiter and ContextCache.
---

# Reliability API

```python
from ytscrape import RetryPolicy, RateLimiter, ContextCache
from ytscrape.context import DEFAULT_CONTEXT_CACHE
```

## `RetryPolicy`

Frozen dataclass.

| Field | Default | Description |
| ----- | ------- | ----------- |
| `max_retries` | `3` | Retries after the first attempt |
| `backoff_factor` | `0.5` | Base for exponential backoff |
| `max_backoff` | `30.0` | Cap for a single delay (s) |
| `jitter` | `True` | Randomise delays |
| `retry_statuses` | `{408, 425, 429, 500, 502, 503, 504}` | HTTP statuses that trigger a retry |
| `retry_on_connection_errors` | `True` | Retry network errors/timeouts |
| `respect_retry_after` | `True` | Honour `Retry-After` |

- `compute_delay(attempt, retry_after=None) -> float`
- `RetryPolicy.disabled() -> RetryPolicy` — no retries.

## `RateLimiter`

`RateLimiter(min_interval=0.0)` — minimal seconds between requests.

- `wait()` — block (sync).
- `async_wait()` — awaitable (async).

## `ContextCache`

`ContextCache(ttl=3600)` — TTL cache of `InnerTubeContext`.

- `get(key) -> InnerTubeContext | None`
- `set(key, context)`
- `invalidate(key=None)` — one key or everything.

`DEFAULT_CONTEXT_CACHE` is the global instance, keyed by `(language, region)`.

## Client parameters

`YouTube`, `AsyncYouTube`, `InnerTubeClient` and `AsyncInnerTubeClient` accept:

| Parameter | Type | Default |
| --------- | ---- | ------- |
| `retry` | `RetryPolicy \| None` | `None` → `RetryPolicy()` |
| `rate_limiter` | `RateLimiter \| None` | `None` |
| `min_interval` | `float` | `0.0` (creates a `RateLimiter` if > 0) |
| `context_cache` | `ContextCache \| bool \| None` | `None` → global cache if the client owns its session |

See the [Reliability guide](../guides/reliability.md).
