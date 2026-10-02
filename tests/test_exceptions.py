"""Tests for the exception hierarchy."""

from __future__ import annotations

import pytest

import ytscrape
from ytscrape import (
    AgeRestricted,
    BotDetected,
    CaptchaRequired,
    ConsentRequired,
    ContextExtractionError,
    NoTranscriptFound,
    ParseError,
    RateLimited,
    RequestError,
    TranscriptError,
    TranscriptsDisabled,
    VideoUnavailable,
    YtScrapeError,
    YtScraperError,
)


def test_base_alias() -> None:
    assert YtScrapeError is YtScraperError
    assert CaptchaRequired is BotDetected


@pytest.mark.parametrize(
    "cls",
    [
        ContextExtractionError,
        RequestError,
        ParseError,
        TranscriptError,
        TranscriptsDisabled,
        NoTranscriptFound,
        RateLimited,
        BotDetected,
        ConsentRequired,
        VideoUnavailable,
        AgeRestricted,
    ],
)
def test_all_subclass_base(cls: type) -> None:
    assert issubclass(cls, YtScrapeError)


def test_request_error_subclasses() -> None:
    for cls in (RateLimited, BotDetected, ConsentRequired):
        assert issubclass(cls, RequestError)
    assert issubclass(AgeRestricted, VideoUnavailable)


def test_attributes() -> None:
    err = RequestError("x", status_code=500, url="u")
    assert (str(err), err.status_code, err.url) == ("x", 500, "u")
    assert RequestError("plain").status_code is None
    rl = RateLimited("slow", retry_after=2.0)
    assert rl.status_code == 429
    assert rl.retry_after == 2.0
    vu = AgeRestricted("vid", "Sign in to confirm your age")
    assert vu.video_id == "vid"
    assert "confirm your age" in str(vu)
    assert str(VideoUnavailable("vid")) == "Video 'vid' is unavailable."


def test_exported() -> None:
    for name in ("RetryPolicy", "RateLimiter", "ContextCache", "YtScrapeError"):
        assert name in ytscrape.__all__
