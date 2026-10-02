---
description: "Reference for the Video, Channel, and Playlist frozen dataclasses and the SearchResults paginated iterator returned by YouTube.search()."
---

# Search result models: Video, Channel, and Playlist

> Reference for the Video, Channel, and Playlist frozen dataclasses and the SearchResults paginated iterator returned by YouTube.search().

When you call `YouTube.search()` it returns a `SearchResults` object. Iterating over it yields one of three frozen dataclass models — `Video`, `Channel`, or `Playlist` — depending on what YouTube returned for that position in the results. All three models are immutable (`frozen=True`) and use `__slots__` for memory efficiency.

## Video

Represents a single video result from a search query.

**`video_id`** (`str`)

:   The unique YouTube video identifier (e.g. `"dQw4w9WgXcQ"`). Never `None`.


**`title`** (`str | None`)

:   The video title as displayed in search results. May be `None` if YouTube did not include it in the response.


**`channel`** (`str | None`)

:   Display name of the uploading channel (e.g. `"Rick Astley"`).


**`channel_id`** (`str | None`)

:   The internal channel identifier that begins with `UC` (e.g. `"UCuAXFkgsw1L7xaCfnd5JJOw"`). Useful for passing to `YouTube.channel()`.


**`duration`** (`str | None`)

:   Human-formatted duration string as shown on YouTube (e.g. `"10:23"` or `"1:02:47"`). `None` for live streams or when unavailable.


**`views`** (`int | None`)

:   View count as an integer (e.g. `1200000`), parsed from the rendered text. The original wording is in **`views_text`** (`str | None`).


**`published_text`** (`str | None`)

:   Relative publication date as shown in search results (e.g. `"3 days ago"`, `"2 years ago"`). `None` for live streams. *(Renamed from `published` in 2.0.)*

**`published_at`** (`datetime | None`)

:   Approximate UTC datetime computed from English `published_text`.


**`thumbnails`** (`tuple[Thumbnail, ...]`)

:   All available sizes as `Thumbnail(url, width, height)`.

**`thumbnail`** (`str | None`)

:   URL of the highest-resolution thumbnail available in the search response.


**`description`** (`str | None`)

:   Short description snippet from `videoRenderer.descriptionSnippet`.


**`url`** (`str`)

:   **Property.** The canonical watch URL constructed from `video_id`: `https://www.youtube.com/watch?v={video_id}`.


***

## Channel

Represents a single channel result from a search query.

**`channel_id`** (`str`)

:   The internal channel identifier (e.g. `"UCuAXFkgsw1L7xaCfnd5JJOw"`). Never `None`.


**`title`** (`str | None`)

:   The channel name (e.g. `"Rick Astley"`).


**`handle`** (`str | None`)

:   The channel's `@handle` if present in the search result (e.g. `"@RickAstleyYT"`).


**`subscribers`** (`int | None`)

:   Subscriber count as an integer. The original wording is in **`subscribers_text`**.


**`video_count`** (`int | None`)

:   Formatted video count as YouTube renders it (e.g. `"142 videos"`).


**`thumbnails`** (`tuple[Thumbnail, ...]`)

:   All available sizes as `Thumbnail(url, width, height)`.

**`thumbnail`** (`str | None`)

:   URL of the channel's avatar thumbnail as returned in the search result.


**`url`** (`str`)

:   **Property.** The canonical channel URL: `https://www.youtube.com/channel/{channel_id}`.


***

## Playlist

Represents a single playlist result from a search query.

**`playlist_id`** (`str`)

:   The unique playlist identifier (e.g. `"PLbpi6ZahtOH6Ar_3GPy3workFpaikFpY3"`). Never `None`.


**`title`** (`str | None`)

:   The playlist title as shown in search results.


**`channel`** (`str | None`)

:   Display name of the channel that owns the playlist.


**`video_count`** (`int | None`)

:   The number of videos in the playlist as a string (e.g. `"42"`).


**`thumbnails`** (`tuple[Thumbnail, ...]`)

:   All available sizes as `Thumbnail(url, width, height)`.

**`thumbnail`** (`str | None`)

:   URL of the playlist's cover thumbnail.


**`url`** (`str`)

:   **Property.** The canonical playlist URL: `https://www.youtube.com/playlist?list={playlist_id}`.


***

## SearchResults

`SearchResults` is the lazy, paginated container returned by `YouTube.search()`. It transparently fetches new pages from YouTube as you consume items, so a simple `for` loop is all you need.

```python
from ytscrape import YouTube

yt = YouTube()
results = yt.search("lo-fi music")

for item in results:
    print(type(item).__name__, item.title)
```

### Properties

**`has_more`** (`bool`)

:   `True` when YouTube has at least one more page of results that can be fetched. Becomes `False` once the continuation token is exhausted.


### Methods

**`to_dict()`** / **`to_json()`** / **`to_csv()`**

:   Serialize every item the iterator would yield (`max_results` still applies). `to_json()` returns a JSON array; `to_csv()` a headered CSV table.


**`dump_json(path)`** / **`dump_csv(path)`**

:   Same payloads, written to a file path or file object.


**`fetch_next_page()`** (`list[Video | Channel | Playlist]`)

:   Explicitly fetches the next page of results, appends them to the internal buffer, and returns the newly added items as a list. Returns an empty list when there are no more pages. Use this when you want fine-grained control over network calls instead of relying on the implicit iterator.

      ```python
      results = yt.search("guitar lessons")

      # Fetch page 2 manually
      page2 = results.fetch_next_page()
      for item in page2:
          print(item.title)
      ```


### Iteration

`SearchResults` is directly iterable. Each iteration step yields a `Video`, `Channel`, or `Playlist` instance. New pages are fetched automatically whenever the internal buffer runs out.

```python
from ytscrape import YouTube
from ytscrape.models import Video, Channel, Playlist

yt = YouTube()

for item in yt.search("python tutorial"):
    if isinstance(item, Video):
        print(f"Video : {item.title}  [{item.duration}]  {item.url}")
    elif isinstance(item, Channel):
        print(f"Channel: {item.title}  ({item.subscribers_text})")
    elif isinstance(item, Playlist):
        print(f"Playlist: {item.title}  — {item.video_count} videos")
```

### Limiting results

Pass `max_results` to `YouTube.search()` to cap how many items are yielded. The iterator stops once that number is reached, even if more pages exist.

```python
# Collect at most 20 results without fetching unnecessary pages
top20 = list(yt.search("synthwave", max_results=20))
```

!!! tip

    `max_results` limits the number of items **yielded by the iterator**, not the number of items fetched per page. YouTube returns roughly 20 results per page, so a `max_results` of 10 still fetches the first full page but stops yielding after 10 items.


***

## AsyncSearchResults

Returned by `await AsyncYouTube.search()`. Same item types (`Video`, `Channel`, `Playlist`) and `has_more` / `max_results` behaviour as `SearchResults`, but iteration and paging are async:

```python
from ytscrape import AsyncYouTube

async with AsyncYouTube() as yt:
    results = await yt.search("lo-fi music", max_results=20)
    async for item in results:
        print(item.title)
    page = await results.fetch_next_page()
    await results.dump_csv("search.csv")
    print(await results.to_json())
```

See the [Async API guide](../guides/async.md).
