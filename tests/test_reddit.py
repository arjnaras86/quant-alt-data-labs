from quantlab.reddit import _mentioned_tickers


def test_detects_cashtag_and_universe_token():
    universe = {"AAPL", "NVDA", "MSFT"}
    assert _mentioned_tickers("Buying $NVDA and AAPL", universe) == {"NVDA", "AAPL"}


def test_ignores_unknown_symbols():
    assert _mentioned_tickers("Buying $FAKE", {"AAPL"}) == set()
