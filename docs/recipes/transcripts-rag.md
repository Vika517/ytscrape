---
description: Fetch YouTube transcripts in Python and split them into timestamped chunks for LLM summarisation or RAG pipelines.
---

# Recipe: transcripts → LLM / RAG chunks

Split a transcript into ~N-second chunks that keep a timestamp link back to the video.

=== "Sync"

    ```python
    from ytscrape import YouTube

    def chunk(transcript, seconds: float = 60.0):
        buf, start = [], None
        for s in transcript.snippets:
            start = s.start if start is None else start
            buf.append(s.text)
            if s.start + s.duration - start >= seconds:
                yield {"start": start, "text": " ".join(buf)}
                buf, start = [], None
        if buf:
            yield {"start": start, "text": " ".join(buf)}

    with YouTube() as yt:
        tr = yt.transcript("dQw4w9WgXcQ", languages=["en"])

    docs = [
        {**c, "url": f"https://youtu.be/{tr.video_id}?t={int(c['start'])}"}
        for c in chunk(tr)
    ]
    # embed docs[i]["text"] with your favourite embedding model / vector store
    ```

=== "Async"

    ```python
    import asyncio
    from ytscrape import AsyncYouTube

    async def main():
        async with AsyncYouTube() as yt:
            return await yt.transcript("dQw4w9WgXcQ", languages=["en"])

    tr = asyncio.run(main())
    ```

Handle `TranscriptsDisabled` and `NoTranscriptFound` for videos without captions.
