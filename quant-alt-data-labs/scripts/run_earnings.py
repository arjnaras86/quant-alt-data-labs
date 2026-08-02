from quantlab.backtest import (
    information_coefficient,
    long_short_backtest,
    performance_summary,
)
from quantlab.earnings import collect_earnings_disclosure_signals
from quantlab.storage import save_frame


# Keep the first test small.
TICKERS = ["AAPL", "MSFT"]

# Increase after confirming the pipeline works.
FILINGS_PER_TICKER = 2


def main() -> None:
    print("=" * 60, flush=True)
    print("SEC Earnings Disclosure Sentiment Research", flush=True)
    print("=" * 60, flush=True)

    print(
        f"Tickers: {', '.join(TICKERS)}",
        flush=True,
    )

    print(
        f"Maximum filings per ticker: {FILINGS_PER_TICKER}",
        flush=True,
    )

    print(
        "\nStarting earnings disclosure collection...",
        flush=True,
    )

    signals = collect_earnings_disclosure_signals(
        tickers=TICKERS,
        filings_per_ticker=FILINGS_PER_TICKER,
    )

    print(
        "\nCollection finished.",
        flush=True,
    )

    if signals.empty:
        print(
            "No earnings signals were generated.",
            flush=True,
        )
        return

    save_frame(
        signals,
        "earnings_signals.csv",
        "earnings_signals",
    )

    print(
        f"Signals generated: {len(signals)}",
        flush=True,
    )

    required_columns = {
        "date",
        "earnings_factor_score",
        "forward_5d_return",
    }

    if not required_columns.issubset(signals.columns):
        missing = required_columns.difference(signals.columns)

        print(
            f"Backtest skipped. Missing columns: {sorted(missing)}",
            flush=True,
        )
        return

    usable = signals.dropna(
        subset=[
            "earnings_factor_score",
            "forward_5d_return",
        ]
    )

    if usable.empty:
        print(
            "Backtest skipped because forward-return data is unavailable.",
            flush=True,
        )
        return

    ic = information_coefficient(
        usable,
        "earnings_factor_score",
        "forward_5d_return",
    )

    print(
        f"Information coefficient: {ic}",
        flush=True,
    )

    backtest = long_short_backtest(
        usable,
        "date",
        "earnings_factor_score",
        "forward_5d_return",
    )

    if backtest.empty:
        print(
            "Backtest produced no rows. This is expected with "
            "only one ticker or a very small sample.",
            flush=True,
        )
        return

    save_frame(
        backtest,
        "earnings_backtest.csv",
        "earnings_backtest",
    )

    summary = performance_summary(
        backtest["strategy_return"],
        periods_per_year=12,
    )

    print(
        "\nPerformance summary:",
        flush=True,
    )

    print(
        summary,
        flush=True,
    )


if __name__ == "__main__":
    main()