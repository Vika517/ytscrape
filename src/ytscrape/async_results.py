"""Async lazy, paginated search results and comment threads.

Mirrors :mod:`ytscrape.results` but uses ``async for`` / ``await``. Parsing is
shared with the sync path via :mod:`ytscrape.parsing`.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from . import parsing
from .export import AsyncExportable
from .models import Channel, Comment, Playlist, Video, bind

__all__ = ["AsyncChannelVideos", "AsyncCommentThread", "AsyncSearchResults"]

SearchItem = Video | Channel | Playlist


class AsyncSearchResults(AsyncExportable):
    """Async iterable view over search results with transparent paging.

    Export with ``await results.dump_csv(...)`` / ``await results.to_json()``.
    """

    def __init__(
        self,
        client: Any,
        first_page: dict[str, Any],
        *,
        max_results: int | None = None,
        youtube: Any = None,
    ) -> None:
        self._client = client
        self._youtube = youtube
        self._continuation: str | None = parsing.find_continuation(first_page)
        self._max_results = max_results
        self._buffer: list[SearchItem] = self._extract_items(first_page)

    def _extract_items(self, page: dict[str, Any]) -> list[SearchItem]:
        items: list[SearchItem] = []
        for key, renderer in parsing.iter_renderers(page):
            item = parsing.parse_item(key, renderer)
            if item is not None:
                items.append(bind(item, self._youtube))
        return items

    async def _fetch_page(self, continuation: str) -> dict[str, Any]:
        return await self._client.search(continuation=continuation)

    @property
    def has_more(self) -> bool:
        """Whether another page can be fetched from YouTube."""
        return self._continuation is not None

    async def fetch_next_page(self) -> list[SearchItem]:
        """Fetch and buffer the next page, returning the newly added items."""
        if self._continuation is None:
            return []
        page = await self._fetch_page(self._continuation)
        self._continuation = parsing.find_continuation(page)
        new_items = self._extract_items(page)
        self._buffer.extend(new_items)
        return new_items

    def __aiter__(self) -> AsyncIterator[SearchItem]:
        return self._iterate()

    async def _iterate(self) -> AsyncIterator[SearchItem]:
        index = 0
        while True:
            if self._max_results is not None and index >= self._max_results:
                return
            if index < len(self._buffer):
                yield self._buffer[index]
                index += 1
                continue
            while not self._buffer[index:] and self.has_more:
                await self.fetch_next_page()
            if index >= len(self._buffer):
                return


class AsyncChannelVideos(AsyncSearchResults):
    """Async paginated uploads of a channel (its *Videos* tab)."""

    def __init__(
        self,
        client: Any,
        channel_id: str,
        first_page: dict[str, Any],
        *,
        max_results: int | None = None,
        youtube: Any = None,
    ) -> None:
        self._channel_id = channel_id
        super().__init__(client, first_page, max_results=max_results, youtube=youtube)

    def _extract_items(self, page: dict[str, Any]) -> list[SearchItem]:
        items = parsing.parse_channel_videos(page, channel_id=self._channel_id)
        return [bind(item, self._youtube) for item in items]

    async def _fetch_page(self, continuation: str) -> dict[str, Any]:
        return await self._client.browse(self._channel_id, continuation=continuation)


class AsyncCommentThread(AsyncExportable):
    """Async iterable view over video comments with transparent paging.

    Export with ``await thread.dump_csv(...)`` / ``await thread.to_json()``.
    """

    def __init__(
        self,
        client: Any,
        first_page: dict[str, Any],
        *,
        max_results: int | None = None,
        include_replies: bool = False,
    ) -> None:
        self._client = client
        self._max_results = max_results
        self._include_replies = include_replies
        self._seen_ids: set[str] = set()
        self._continuation: str | None = parsing.find_next_comments_continuation(
            first_page
        )
        self._buffer: list[Comment] = []
        self._initialized = False
        self._first_page = first_page

    def _dedupe(self, comments: list[Comment]) -> list[Comment]:
        unique: list[Comment] = []
        for comment in comments:
            if comment.comment_id and comment.comment_id in self._seen_ids:
                continue
            if comment.comment_id:
                self._seen_ids.add(comment.comment_id)
            unique.append(comment)
        return unique

    async def _collect(self, page: dict[str, Any]) -> list[Comment]:
        top_level = self._dedupe(parsing.parse_comments_page(page))
        if not self._include_replies:
            return top_level

        replies_by_parent: dict[str, list[Comment]] = {}
        orphan_replies: list[Comment] = []
        for parent_id, token in parsing.find_reply_continuations(page):
            replies = await self._fetch_replies(token)
            if parent_id:
                replies_by_parent.setdefault(parent_id, []).extend(replies)
            else:
                orphan_replies.extend(replies)

        collected: list[Comment] = []
        for comment in top_level:
            collected.append(comment)
            collected.extend(replies_by_parent.pop(comment.comment_id, []))
        for leftover in replies_by_parent.values():
            collected.extend(leftover)
        collected.extend(orphan_replies)
        return collected

    async def _fetch_replies(self, token: str | None) -> list[Comment]:
        replies: list[Comment] = []
        while token is not None:
            page = await self._client.next(continuation=token)
            replies.extend(
                self._dedupe(parsing.parse_comments_page(page, force_reply=True))
            )
            token = parsing.find_next_comments_continuation(page)
        return replies

    async def _ensure_initialized(self) -> None:
        if self._initialized:
            return
        self._buffer = await self._collect(self._first_page)
        self._initialized = True

    @property
    def has_more(self) -> bool:
        """Whether another page of comments can be fetched from YouTube."""
        return self._continuation is not None

    async def fetch_next_page(self) -> list[Comment]:
        """Fetch and buffer the next page, returning the newly added comments."""
        await self._ensure_initialized()
        if self._continuation is None:
            return []
        page = await self._client.next(continuation=self._continuation)
        self._continuation = parsing.find_next_comments_continuation(page)
        new_items = await self._collect(page)
        self._buffer.extend(new_items)
        return new_items

    def __aiter__(self) -> AsyncIterator[Comment]:
        return self._iterate()

    async def _iterate(self) -> AsyncIterator[Comment]:
        await self._ensure_initialized()
        index = 0
        while True:
            if self._max_results is not None and index >= self._max_results:
                return
            if index < len(self._buffer):
                yield self._buffer[index]
                index += 1
                continue
            while not self._buffer[index:] and self.has_more:
                await self.fetch_next_page()
            if index >= len(self._buffer):
                return
