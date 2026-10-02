"""Playability checks and client option pass-through on the facades."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from ytscrape import AsyncYouTube, YouTube
from ytscrape.client import RateLimiter, RetryPolicy
from ytscrape.context import ContextCache
from ytscrape.exceptions import AgeRestricted, BotDetected, VideoUnavailable

VIDEO_ID = "dQw4w9WgXcQ"

UNAVAILABLE = {"playabilityStatus": {"status": "ERROR", "reason": "Video unavailable"}}
AGE = {
    "playabilityStatus": {
        "status": "LOGIN_REQUIRED",
        "reason": "Sign in to confirm your age",
    }
}
BOT = {
    "playabilityStatus": {
        "status": "LOGIN_REQUIRED",
        "reason": "Sign in to confirm you're not a bot",
    }
}
CASES = [
    (UNAVAILABLE, VideoUnavailable),
    (AGE, AgeRestricted),
    (BOT, BotDetected),
]


class _SyncClient:
    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response

    def player(self, video_id: str, **_: Any) -> dict[str, Any]:
        return self.response


class _AsyncClient:
    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response

    async def player(self, video_id: str, **_: Any) -> dict[str, Any]:
        return self.response


@pytest.mark.parametrize(("response", "exc"), CASES)
def test_sync_video_checks_playability(
    response: dict[str, Any], exc: type[Exception]
) -> None:
    yt = YouTube(client=_SyncClient(response))  # type: ignore[arg-type]
    with pytest.raises(exc):
        yt.video(VIDEO_ID)


@pytest.mark.parametrize(("response", "exc"), CASES)
def test_async_video_checks_playability(
    response: dict[str, Any], exc: type[Exception]
) -> None:
    yt = AsyncYouTube(client=_AsyncClient(response))  # type: ignore[arg-type]
    with pytest.raises(exc):
        asyncio.run(yt.video(VIDEO_ID))


def _options() -> dict[str, Any]:
    return {
        "retry": RetryPolicy(),
        "min_interval": 0.25,
        "rate_limiter": RateLimiter(0.5),
        "context_cache": ContextCache(),
    }


def _assert_forwarded(captured: dict[str, Any], opts: dict[str, Any]) -> None:
    for key, value in opts.items():
        assert captured[key] is value or captured[key] == value


def test_sync_constructor_forwards_client_options(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    class Recorder:
        def __init__(self, **kwargs: Any) -> None:
            captured.update(kwargs)

    monkeypatch.setattr("ytscrape.youtube.InnerTubeClient", Recorder)
    opts = _options()
    YouTube(**opts)
    _assert_forwarded(captured, opts)


def test_async_constructor_forwards_client_options(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    class Recorder:
        def __init__(self, **kwargs: Any) -> None:
            captured.update(kwargs)

    monkeypatch.setattr("ytscrape.async_youtube.AsyncInnerTubeClient", Recorder)
    opts = _options()
    AsyncYouTube(**opts)
    _assert_forwarded(captured, opts)
