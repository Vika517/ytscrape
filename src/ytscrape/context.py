"""Extraction of the YouTube InnerTube context.

The InnerTube API needs three values that YouTube embeds into the HTML of its
home page: an API key, the client version and the ``visitorData`` token. This
module isolates the scraping of those values behind a small, testable object.
"""

from __future__ import annotations

import re
import threading
import time
from collections.abc import Hashable
from dataclasses import dataclass
from typing import ClassVar

__all__ = [
    "DEFAULT_CONTEXT_CACHE",
    "ContextCache",
    "ContextExtractor",
    "InnerTubeContext",
]


@dataclass(frozen=True, slots=True)
class InnerTubeContext:
    """The set of values required to talk to the InnerTube API."""

    api_key: str
    client_version: str
    visitor_data: str


class ContextExtractor:
    """Extract an :class:`InnerTubeContext` from YouTube home page HTML.

    The regular expressions live here so that the networking client only has to
    hand over raw HTML and receive a ready-to-use context back.
    """

    _PATTERNS: ClassVar[dict[str, str]] = {
        "api_key": r'"INNERTUBE_API_KEY":"([^"]+)"',
        "client_version": r'"INNERTUBE_CLIENT_VERSION":"([^"]+)"',
        "visitor_data": r'"(?:VISITOR_DATA|visitorData)":"([^"]+)"',
    }

    def extract(self, html: str) -> InnerTubeContext:
        """Parse ``html`` and return the extracted :class:`InnerTubeContext`.

        Raises:
            ContextExtractionError: If any required value is missing.
        """
        # Imported lazily to keep this module free of package-level cycles.
        from .exceptions import ContextExtractionError, with_block_mitigation

        values: dict[str, str] = {}
        for name, pattern in self._PATTERNS.items():
            match = re.search(pattern, html)
            if not match:
                raise ContextExtractionError(
                    with_block_mitigation(
                        f"Unable to find {name!r} in YouTube response "
                        "(page may be a consent wall, captcha, or bot check)"
                    )
                )
            values[name] = match.group(1)

        return InnerTubeContext(
            api_key=values["api_key"],
            client_version=values["client_version"],
            visitor_data=values["visitor_data"],
        )


class ContextCache:
    """Thread-safe in-memory TTL cache of :class:`InnerTubeContext` objects.

    Keys are arbitrary hashables (the clients use ``(language, region)``).

    Args:
        ttl: Lifetime of an entry in seconds. ``0`` or negative disables
            caching (``get`` always misses).
    """

    def __init__(self, ttl: float = 3600.0) -> None:
        self.ttl = ttl
        self._data: dict[Hashable, tuple[float, InnerTubeContext]] = {}
        self._lock = threading.Lock()

    def get(self, key: Hashable) -> InnerTubeContext | None:
        """Return a fresh cached context for ``key`` or ``None``."""
        if self.ttl <= 0:
            return None
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return None
            stored_at, context = entry
            if time.monotonic() - stored_at > self.ttl:
                del self._data[key]
                return None
            return context

    def set(self, key: Hashable, context: InnerTubeContext) -> None:
        """Store ``context`` under ``key``."""
        if self.ttl <= 0:
            return
        with self._lock:
            self._data[key] = (time.monotonic(), context)

    def invalidate(self, key: Hashable | None = None) -> None:
        """Drop one entry, or every entry when ``key`` is ``None``."""
        with self._lock:
            if key is None:
                self._data.clear()
            else:
                self._data.pop(key, None)

    def __len__(self) -> int:
        with self._lock:
            return len(self._data)


#: Process-wide cache used by clients that own their HTTP session.
DEFAULT_CONTEXT_CACHE = ContextCache()
