from quantlab.sentiment import normalize_text, score_text


def test_normalize_text_collapses_whitespace():
    assert normalize_text("hello\n  world") == "hello world"


def test_score_text_returns_expected_features():
    result = score_text("Strong growth, but uncertainty and risk remain.")
    assert result["word_count"] > 0
    assert result["uncertainty_count"] == 2
    assert -1 <= result["compound_sentiment"] <= 1
