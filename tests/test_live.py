"""Live smoke tests against the real YouTube.

Skipped by default. Run with::

    uv run pytest --run-network -m network

They check the *shape* of the data (types, non-empty fields), not exact
values, so changing view counts do not break them.
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime

import pytest

from ytscrape import VideoUnavailable, YouTube

pytestmark = pytest.mark.network

VIDEO_ID = "dQw4w9WgXcQ"
CHANNEL = "@RickAstleyYT"


@pytest.fixture(scope="module")
def yt() -> Iterator[YouTube]:
    with YouTube(language="en", region="US") as client:
        yield client


def test_search(yt: YouTube) -> None:
    videos = list(yt.search("python tutorial", max_results=5))
    assert videos
    assert all(v.title for v in videos)
    assert any(isinstance(getattr(v, "views", None), int) for v in videos)


def test_video_details(yt: YouTube) -> None:
    details = yt.video(VIDEO_ID)
    assert details.title
    assert details.channel
    assert isinstance(details.views, int)
    assert details.views > 0
    assert isinstance(details.published_at, datetime)
    assert details.thumbnails


def test_channel(yt: YouTube) -> None:
    channel = yt.channel(CHANNEL)
    assert channel.title
    assert channel.subscribers is None or channel.subscribers > 0


def test_channel_videos(yt: YouTube) -> None:
    videos = list(yt.channel_videos(CHANNEL, max_results=5))
    assert videos
    assert all(v.video_id for v in videos)


def test_comments(yt: YouTube) -> None:
    comments = list(yt.comments(VIDEO_ID, max_results=5))
    assert comments
    assert all(c.text for c in comments)


def test_transcript(yt: YouTube) -> None:
    transcript = yt.transcript(VIDEO_ID)
    assert list(transcript)


def test_unavailable_video(yt: YouTube) -> None:
    with pytest.raises(VideoUnavailable):
        yt.video("aaaaaaaaaaa")
