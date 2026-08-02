from __future__ import annotations

import math
import re
from collections.abc import Iterator

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
except ImportError:
    SentimentIntensityAnalyzer = None


class _FallbackAnalyzer:
    """
    Basic sentiment fallback used only when vaderSentiment
    is unavailable.
    """

    POSITIVE = {
        "strong",
        "growth",
        "gain",
        "improve",
        "improved",
        "positive",
        "beat",
        "increase",
        "increased",
        "profit",
        "profitable",
        "opportunity",
    }

    NEGATIVE = {
        "risk",
        "uncertainty",
        "weakness",
        "decline",
        "declined",
        "loss",
        "negative",
        "pressure",
        "slowdown",
        "litigation",
    }

    def polarity_scores(self, text: str) -> dict[str, float]:
        tokens = re.findall(r"[A-Za-z']+", text.lower())

        positive_count = sum(
            token in self.POSITIVE
            for token in tokens
        )

        negative_count = sum(
            token in self.NEGATIVE
            for token in tokens
        )

        total = max(len(tokens), 1)
        sentiment_total = max(
            positive_count + negative_count,
            1,
        )

        compound = (
            positive_count - negative_count
        ) / sentiment_total

        positive_rate = positive_count / total
        negative_rate = negative_count / total
        neutral_rate = max(
            1.0 - positive_rate - negative_rate,
            0.0,
        )

        return {
            "compound": compound,
            "pos": positive_rate,
            "neg": negative_rate,
            "neu": neutral_rate,
        }


_ANALYZER = (
    SentimentIntensityAnalyzer()
    if SentimentIntensityAnalyzer
    else _FallbackAnalyzer()
)


UNCERTAINTY_WORDS = {
    "adverse",
    "challenge",
    "challenges",
    "challenging",
    "concern",
    "concerns",
    "decline",
    "declines",
    "headwind",
    "headwinds",
    "inflation",
    "litigation",
    "pressure",
    "pressures",
    "risk",
    "risks",
    "slowdown",
    "uncertain",
    "uncertainty",
    "volatile",
    "volatility",
    "weakness",
}


# VADER is much faster when long documents are analyzed in chunks.
CHUNK_CHARACTER_LIMIT = 4_000

# SEC filings can contain exhibits, tables and duplicated HTML.
# Limiting the analyzed text keeps the project responsive.
MAX_DOCUMENT_CHARACTERS = 250_000


def normalize_text(text: str) -> str:
    """
    Remove repeated whitespace from filing text.
    """
    return re.sub(
        r"\s+",
        " ",
        text or "",
    ).strip()


def chunk_text(
    text: str,
    chunk_size: int = CHUNK_CHARACTER_LIMIT,
) -> Iterator[str]:
    """
    Split text into manageable chunks without cutting words
    whenever possible.
    """
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(
            start + chunk_size,
            text_length,
        )

        if end < text_length:
            last_space = text.rfind(
                " ",
                start,
                end,
            )

            if last_space > start:
                end = last_space

        chunk = text[start:end].strip()

        if chunk:
            yield chunk

        start = end

        while (
            start < text_length
            and text[start].isspace()
        ):
            start += 1


def score_text(text: str) -> dict[str, float | int | bool]:
    """
    Calculate sentiment and uncertainty features for a filing.

    Long documents are truncated and evaluated in chunks so VADER
    does not become unreasonably slow.
    """
    clean = normalize_text(text)

    original_character_count = len(clean)

    analyzed_text = clean[
        :MAX_DOCUMENT_CHARACTERS
    ]

    was_truncated = (
        original_character_count
        > MAX_DOCUMENT_CHARACTERS
    )

    tokens = re.findall(
        r"[A-Za-z']+",
        analyzed_text.lower(),
    )

    word_count = len(tokens)

    uncertainty_count = sum(
        token in UNCERTAINTY_WORDS
        for token in tokens
    )

    weighted_compound = 0.0
    weighted_positive = 0.0
    weighted_negative = 0.0
    weighted_neutral = 0.0
    total_chunk_words = 0
    chunk_count = 0

    for chunk in chunk_text(analyzed_text):
        chunk_word_count = len(
            re.findall(
                r"[A-Za-z']+",
                chunk,
            )
        )

        if chunk_word_count == 0:
            continue

        scores = _ANALYZER.polarity_scores(
            chunk
        )

        weighted_compound += (
            scores["compound"]
            * chunk_word_count
        )

        weighted_positive += (
            scores["pos"]
            * chunk_word_count
        )

        weighted_negative += (
            scores["neg"]
            * chunk_word_count
        )

        weighted_neutral += (
            scores["neu"]
            * chunk_word_count
        )

        total_chunk_words += chunk_word_count
        chunk_count += 1

    if total_chunk_words == 0:
        compound_sentiment = 0.0
        positive = 0.0
        negative = 0.0
        neutral = 1.0

    else:
        compound_sentiment = (
            weighted_compound
            / total_chunk_words
        )

        positive = (
            weighted_positive
            / total_chunk_words
        )

        negative = (
            weighted_negative
            / total_chunk_words
        )

        neutral = (
            weighted_neutral
            / total_chunk_words
        )

    uncertainty_rate = (
        uncertainty_count / word_count
        if word_count
        else 0.0
    )

    return {
        "compound_sentiment": compound_sentiment,
        "positive": positive,
        "negative": negative,
        "neutral": neutral,
        "uncertainty_count": uncertainty_count,
        "uncertainty_rate": uncertainty_rate,
        "word_count": word_count,
        "log_word_count": math.log1p(word_count),
        "sentiment_chunk_count": chunk_count,
        "original_character_count": original_character_count,
        "analyzed_character_count": len(analyzed_text),
        "text_was_truncated": was_truncated,
    }