from __future__ import annotations

import re

import pandas as pd
from quantlab.config import settings
from quantlab.market import add_forward_returns
from quantlab.sentiment import score_text


def _mentioned_tickers(text: str, ticker_universe: set[str]) -> set[str]:
    explicit = {match.upper() for match in re.findall(r"\$([A-Za-z]{1,5})\b", text)}
    tokens = {token.upper() for token in re.findall(r"\b[A-Za-z]{2,5}\b", text)}
    # Plain-token matches are limited to the supplied universe to reduce false positives.
    return (explicit | tokens) & ticker_universe


def collect_reddit_signals(
    tickers: list[str],
    subreddits: list[str],
    listing: str = "new",
    limit: int = 250,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    settings.require_reddit()
    import praw

    reddit = praw.Reddit(
        client_id=settings.reddit_client_id,
        client_secret=settings.reddit_client_secret,
        user_agent=settings.reddit_user_agent,
        check_for_async=False,
    )
    universe = {ticker.upper() for ticker in tickers}
    rows: list[dict] = []

    for subreddit_name in subreddits:
        subreddit = reddit.subreddit(subreddit_name)
        iterator = getattr(subreddit, listing)(limit=limit)
        for post in iterator:
            text = f"{post.title or ''} {post.selftext or ''}"
            mentions = _mentioned_tickers(text, universe)
            if not mentions:
                continue
            features = score_text(text)
            for ticker in mentions:
                rows.append(
                    {
                        "ticker": ticker,
                        "subreddit": subreddit_name,
                        "post_id": post.id,
                        "created_utc": post.created_utc,
                        "date": pd.to_datetime(post.created_utc, unit="s", utc=True).tz_convert(None).normalize(),
                        "title": post.title,
                        "post_score": post.score,
                        "comment_count": post.num_comments,
                        "upvote_ratio": getattr(post, "upvote_ratio", None),
                        "url": f"https://www.reddit.com{post.permalink}",
                        **features,
                    }
                )

    raw = pd.DataFrame(rows)
    if raw.empty:
        return raw, raw

    signals = (
        raw.groupby(["ticker", "date"], as_index=False)
        .agg(
            mention_count=("post_id", "nunique"),
            subreddit_count=("subreddit", "nunique"),
            average_sentiment=("compound_sentiment", "mean"),
            average_negative=("negative", "mean"),
            total_post_score=("post_score", "sum"),
            total_comments=("comment_count", "sum"),
        )
    )
    import numpy as np
    signals["reddit_factor_score"] = (
        signals["average_sentiment"]
        - 0.5 * signals["average_negative"]
        + 0.15 * np.log1p(signals["mention_count"])
        + 0.05 * np.log1p(signals["total_comments"].clip(lower=0))
    )
    signals = add_forward_returns(signals, horizons=(1, 5, 20))
    return raw, signals
