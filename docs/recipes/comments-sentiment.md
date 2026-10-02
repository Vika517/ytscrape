---
description: Scrape YouTube comments with Python into a pandas DataFrame and run a quick sentiment analysis — no API key needed.
---

# Recipe: comments → pandas → sentiment

```bash
pip install ytscrape pandas vaderSentiment
```

=== "Sync"

    ```python
    import pandas as pd
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    from ytscrape import CommentSort, YouTube, to_dict

    with YouTube() as yt:
        comments = list(yt.comments("dQw4w9WgXcQ", max_results=500, sort=CommentSort.TOP))

    df = pd.DataFrame([to_dict(c) for c in comments])
    analyzer = SentimentIntensityAnalyzer()
    df["sentiment"] = df["text"].fillna("").map(lambda t: analyzer.polarity_scores(t)["compound"])
    print(df[["author", "like_count", "sentiment"]].sort_values("like_count", ascending=False).head())
    print("Mean sentiment:", df["sentiment"].mean())
    ```

=== "Async"

    ```python
    import asyncio
    import pandas as pd
    from ytscrape import AsyncYouTube, to_dict

    async def main() -> pd.DataFrame:
        async with AsyncYouTube() as yt:
            thread = await yt.comments("dQw4w9WgXcQ", max_results=500)
            return pd.DataFrame([to_dict(c) async for c in thread])

    df = asyncio.run(main())
    ```

`like_count` and `reply_count` are integers, so you can sort and aggregate directly.
