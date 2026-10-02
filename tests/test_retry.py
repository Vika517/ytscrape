"""Tests for retries, rate limiting, context caching and block detection."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import pytest
import requests

import ytscrape.client as client_mod
from ytscrape import (
    AgeRestricted,
    BotDetected,
    ConsentRequired,
    ContextCache,
    InnerTubeClient,
    InnerTubeContext,
    RateLimited,
    RateLimiter,
    RequestError,
    RetryPolicy,
    VideoUnavailable,
)
from ytscrape.async_client import AsyncInnerTubeClient
from ytscrape.client import check_playability, detect_block, parse_retry_after

_HOME = (
    '"INNERTUBE_API_KEY":"KEY","INNERTUBE_CLIENT_VERSION":"1.2.3","VISITOR_DATA":"VD"'
)


class Resp:
    def __init__(
        self,
        status_code: int = 200,
        *,
        text: str = _HOME,
        data: Any = None,
        headers: dict[str, str] | None = None,
        url: str = "https://www.youtube.com/",
    ) -> None:
        self.status_code = status_code
        self.text = text
        self._data = data if data is not None else {"ok": True}
        self.headers = headers or {}
        self.url = url

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")

    def json(self) -> Any:
        return self._data


class ScriptedSession:
    """Serves queued responses (or raises queued exceptions) for POST."""

    def __init__(self, post_script: list[Any], get_script: list[Any] | None = None):
        self.post_script = list(post_script)
        self.get_script = list(get_script or [])
        self.posts = 0
        self.gets = 0

    def _next(self, script: list[Any]) -> Any:
        item = script.pop(0) if len(script) > 1 else script[0]
        if isinstance(item, Exception):
            raise item
        return item

    def get(self, url: str, **kwargs: Any) -> Any:
        self.gets += 1
        return self._next(self.get_script or [Resp()])

    def post(self, url: str, **kwargs: Any) -> Any:
        self.posts += 1
        return self._next(self.post_script)

    def close(self) -> None:
        pass


@pytest.fixture
def sleeps(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    recorded: list[float] = []
    monkeypatch.setattr(client_mod.time, "sleep", recorded.append)
    return recorded


_FAST = RetryPolicy(max_retries=3, backoff_factor=0.1, jitter=False)


class TestRetryPolicy:
    def test_exponential_without_jitter(self) -> None:
        p = RetryPolicy(backoff_factor=1.0, max_backoff=5.0, jitter=False)
        assert [p.compute_delay(i) for i in range(4)] == [1.0, 2.0, 4.0, 5.0]

    def test_jitter_bounds(self) -> None:
        p = RetryPolicy(backoff_factor=1.0)
        for _ in range(50):
            assert 0.5 <= p.compute_delay(0) <= 1.0

    def test_retry_after_overrides_and_is_capped(self) -> None:
        p = RetryPolicy(max_backoff=10.0)
        assert p.compute_delay(0, 3.0) == 3.0
        assert p.compute_delay(0, 100.0) == 10.0
        assert (
            RetryPolicy(respect_retry_after=False, jitter=False).compute_delay(0, 3.0)
            == 0.5
        )

    def test_validation(self) -> None:
        with pytest.raises(ValueError, match="max_retries"):
            RetryPolicy(max_retries=-1)
        with pytest.raises(ValueError, match="backoff_factor"):
            RetryPolicy(backoff_factor=-1)
        assert RetryPolicy.disabled().max_retries == 0

    def test_parse_retry_after(self) -> None:
        assert parse_retry_after("5") == 5.0
        assert parse_retry_after(None) is None
        assert parse_retry_after("garbage") is None
        assert parse_retry_after("Wed, 21 Oct 2015 07:28:00 GMT") == 0.0


class TestSyncRetries:
    def test_retries_5xx_then_succeeds(self, sleeps: list[float]) -> None:
        session = ScriptedSession([Resp(503), Resp(502), Resp(data={"r": 1})])
        client = InnerTubeClient(session=session, retry=_FAST)
        assert client.search("q") == {"r": 1}
        assert session.posts == 3
        assert sleeps == [0.1, 0.2]

    def test_honours_retry_after(self, sleeps: list[float]) -> None:
        session = ScriptedSession(
            [Resp(429, headers={"Retry-After": "2"}), Resp(data={"r": 1})]
        )
        client = InnerTubeClient(session=session, retry=_FAST)
        client.search("q")
        assert sleeps == [2.0]

    def test_rate_limited_after_exhausting(self, sleeps: list[float]) -> None:
        session = ScriptedSession([Resp(429, headers={"Retry-After": "1"})])
        client = InnerTubeClient(session=session, retry=_FAST)
        with pytest.raises(RateLimited) as info:
            client.search("q")
        assert info.value.retry_after == 1.0
        assert info.value.status_code == 429
        assert session.posts == 4

    def test_5xx_exhausted_raises_request_error(self, sleeps: list[float]) -> None:
        session = ScriptedSession([Resp(500)])
        client = InnerTubeClient(session=session, retry=_FAST)
        with pytest.raises(RequestError) as info:
            client.search("q")
        assert info.value.status_code == 500

    def test_connection_errors_retried(self, sleeps: list[float]) -> None:
        session = ScriptedSession(
            [requests.ConnectionError("down"), requests.Timeout("slow"), Resp()]
        )
        client = InnerTubeClient(session=session, retry=_FAST)
        assert client.search("q") == {"ok": True}
        assert session.posts == 3

    def test_404_not_retried(self, sleeps: list[float]) -> None:
        session = ScriptedSession([Resp(404)])
        client = InnerTubeClient(session=session, retry=_FAST)
        with pytest.raises(RequestError):
            client.search("q")
        assert session.posts == 1
        assert sleeps == []

    def test_disabled_policy(self, sleeps: list[float]) -> None:
        session = ScriptedSession([requests.ConnectionError("down")])
        client = InnerTubeClient(session=session, retry=RetryPolicy.disabled())
        with pytest.raises(RequestError):
            client.search("q")
        assert session.posts == 1

    def test_debug_logging(
        self, sleeps: list[float], caplog: pytest.LogCaptureFixture
    ) -> None:
        session = ScriptedSession([Resp(503), Resp()])
        client = InnerTubeClient(session=session, retry=_FAST)
        with caplog.at_level(logging.DEBUG, logger="ytscrape"):
            client.search("q")
        text = caplog.text
        assert "retrying" in text
        assert "-> 200" in text


class TestRateLimiter:
    def test_reserve_spaces_requests(self) -> None:
        limiter = RateLimiter(10.0)
        assert limiter.reserve() == 0.0
        assert 9.0 < limiter.reserve() <= 10.0

    def test_disabled(self) -> None:
        limiter = RateLimiter()
        assert limiter.reserve() == 0.0
        assert limiter.reserve() == 0.0
        with pytest.raises(ValueError, match="min_interval"):
            RateLimiter(-1)

    def test_client_waits(self, sleeps: list[float]) -> None:
        session = ScriptedSession([Resp()])
        client = InnerTubeClient(session=session, min_interval=5.0)
        client.search("q")  # GET home + POST
        assert len(sleeps) == 1
        assert sleeps[0] > 4.0


class TestContextCache:
    def test_ttl_expiry(self, monkeypatch: pytest.MonkeyPatch) -> None:
        now = [100.0]
        monkeypatch.setattr("ytscrape.context.time.monotonic", lambda: now[0])
        cache = ContextCache(ttl=10)
        ctx = InnerTubeContext("k", "v", "d")
        cache.set(("en", "US"), ctx)
        assert cache.get(("en", "US")) is ctx
        now[0] = 111.0
        assert cache.get(("en", "US")) is None

    def test_disabled_and_invalidate(self) -> None:
        off = ContextCache(ttl=0)
        off.set("k", InnerTubeContext("a", "b", "c"))
        assert off.get("k") is None
        cache = ContextCache()
        cache.set("k", InnerTubeContext("a", "b", "c"))
        cache.invalidate()
        assert len(cache) == 0

    def test_clients_share_cache_per_locale(self) -> None:
        cache = ContextCache()
        s1, s2, s3 = (
            ScriptedSession([Resp()]),
            ScriptedSession([Resp()]),
            ScriptedSession([Resp()]),
        )
        InnerTubeClient(session=s1, context_cache=cache).search("q")
        InnerTubeClient(session=s2, context_cache=cache).search("q")
        InnerTubeClient(session=s3, context_cache=cache, language="de").search("q")
        assert (s1.gets, s2.gets, s3.gets) == (1, 0, 1)

    def test_injected_session_does_not_use_global_cache(self) -> None:
        s1, s2 = ScriptedSession([Resp()]), ScriptedSession([Resp()])
        InnerTubeClient(session=s1).search("q")
        InnerTubeClient(session=s2).search("q")
        assert (s1.gets, s2.gets) == (1, 1)


class TestBlockDetection:
    def test_consent_redirect(self) -> None:
        session = ScriptedSession(
            [Resp()],
            get_script=[Resp(url="https://consent.youtube.com/m?continue=x")],
        )
        with pytest.raises(ConsentRequired):
            _ = InnerTubeClient(session=session).context

    def test_google_sorry(self) -> None:
        with pytest.raises(BotDetected):
            detect_block("https://www.google.com/sorry/index?continue=x")

    def test_bot_check_page(self) -> None:
        session = ScriptedSession(
            [Resp()],
            get_script=[Resp(text="<p>Sign in to confirm you\u2019re not a bot</p>")],
        )
        with pytest.raises(BotDetected):
            InnerTubeClient(session=session).get_html("https://www.youtube.com/x")

    def test_normal_page_passes(self) -> None:
        detect_block("https://www.youtube.com/", "<html>hello</html>", 200)

    def test_player_bot_check(self) -> None:
        data = {
            "playabilityStatus": {
                "status": "LOGIN_REQUIRED",
                "reason": "Sign in to confirm you're not a bot",
            }
        }
        session = ScriptedSession([Resp(data=data)])
        with pytest.raises(BotDetected):
            InnerTubeClient(session=session).player("abc")

    def test_check_playability(self) -> None:
        check_playability({"playabilityStatus": {"status": "OK"}}, "v")
        check_playability({}, "v")
        with pytest.raises(AgeRestricted):
            check_playability(
                {
                    "playabilityStatus": {
                        "status": "LOGIN_REQUIRED",
                        "reason": "Sign in to confirm your age",
                    }
                },
                "v",
            )
        with pytest.raises(VideoUnavailable) as info:
            check_playability(
                {
                    "playabilityStatus": {
                        "status": "ERROR",
                        "reason": "Video unavailable",
                    }
                },
                "v",
            )
        assert not isinstance(info.value, AgeRestricted)
        assert info.value.video_id == "v"


class TestAsyncSharedPolicy:
    def test_backward_compatible_params(self) -> None:
        pytest.importorskip("httpx")
        client = AsyncInnerTubeClient(
            session=object(), max_retries=5, backoff_factor=0.1
        )
        assert client.retry_policy.max_retries == 5
        assert client.retry_policy.backoff_factor == 0.1
        with pytest.raises(ValueError, match="max_retries"):
            AsyncInnerTubeClient(session=object(), max_retries=-1)

    def test_async_rate_limited_and_retry_after(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        pytest.importorskip("httpx")
        delays: list[float] = []

        async def fake_sleep(delay: float) -> None:
            delays.append(delay)

        monkeypatch.setattr("ytscrape.async_client.asyncio.sleep", fake_sleep)

        class Session:
            async def request(self, method: str, url: str, **kwargs: Any) -> Any:
                if "youtubei" in url:
                    return Resp(429, headers={"Retry-After": "3"})
                return Resp()

        client = AsyncInnerTubeClient(
            session=Session(), retry=RetryPolicy(max_retries=2, jitter=False)
        )
        with pytest.raises(RateLimited):
            asyncio.run(client.search("q"))
        assert delays == [3.0, 3.0]

    def test_async_consent_detected(self) -> None:
        pytest.importorskip("httpx")

        class Session:
            async def request(self, method: str, url: str, **kwargs: Any) -> Any:
                return Resp(url="https://consent.youtube.com/ml")

        client = AsyncInnerTubeClient(session=Session())
        with pytest.raises(ConsentRequired):
            asyncio.run(client.get_context())
