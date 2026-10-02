# TODO

What's left in **ytscrape**. Rough priority order within each section.
`[ ]` — not yet · 🔥 — release blocker.


## InnerTube coverage

- [ ] Channel tabs: videos, shorts, live, playlists *(videos tab done — `channel_videos()`)*
- [ ] Playlist items (`yt.playlist()`)
- [ ] Related videos
- [ ] Trending / home feed
- [ ] Community posts
- [ ] Search filters: upload date, duration, features, sort
- [ ] Search within a channel or playlist
- [ ] Search suggestions

## Reliability

- [x] Built-in retries + exponential backoff on **sync** `InnerTubeClient` (429 / 5xx)
  *(async client already has retries / backoff / concurrency)*
- [x] Rate limiting option (sync + shared policy)
- [x] Cached InnerTube context with TTL
- [x] Detect captcha / consent / bot checks
- [x] Richer exception hierarchy beyond `ParseError`
  *(transcript errors already exist: `TranscriptsDisabled`, `NoTranscriptFound`)*
- [x] Optional request logging / debug mode

## Models

- [x] Numeric fields where search/list APIs still return strings
  *(e.g. `Video.views`, `Channel.subscribers`; `VideoDetails.views` is already `int`)*
- [x] Parsed `published_at: datetime` where available
- [x] Navigation helpers: `video.comments()`, `video.channel()`, `channel.videos()`
- [x] `.to_dict()` / `.to_json()` (or shared serializers)
- [x] Thumbnails as a list of sizes (not only largest URL)

## CLI

- [x] `--json` / `--csv` output (`--format json|csv`)
  *(`--jsonl` still open)*
- [ ] Commands for playlist, trending, channel tabs (after library APIs)
- [x] `--output` / `-o`
  *(`--quiet`, `--limit`, stable exit codes still open)*
- [x] Progress for long collections (braille spinner in table mode)
- [x] Split CLI helpers out of `__main__.py` into `_cli.py`
  *(handlers/formatters still live in `__main__.py`)*

## Tests & CI

- [x] 🔥 Run `pytest` in CI (today only pre-commit)
- [x] Python 3.10–3.14 matrix
- [x] Coverage + Codecov badge
- [x] `mypy` / typecheck in CI (when ready)
- [x] Network-marked live tests (nightly / manual)
- [ ] Snapshot fixtures of real InnerTube responses
- [x] Dependabot / scheduled `pre-commit autoupdate`

## Docs
- [x] Examples / guide for CSV/JSON export
  *(playlist examples still open)*
- [x] CLI demo GIF in the README
- [ ] Optional benchmarks vs `yt-dlp` / Playwright
