from quantlab.backtest import (
    information_coefficient,
    long_short_backtest,
    performance_summary,
)
from quantlab.insiders import collect_insider_signals
from quantlab.storage import save_frame


# Start with one ticker while testing.
TICKERS = ["AAPL", "MSFT"]

# Start with only three filings.
# Increase this after confirming the script works.
FILINGS_PER_TICKER = 3


def main() -> None:
    print("=" * 60, flush=True)
    print("SEC Insider Transaction Research", flush=True)
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
        "\nStarting insider data collection...",
        flush=True,
    )

    raw, signals = collect_insider_signals(
        tickers=TICKERS,
        filings_per_ticker=FILINGS_PER_TICKER,
    )

    print(
        "\nSEC collection finished.",
        flush=True,
    )

    if raw.empty:
        print(
            "No transactions were collected. "
            "No output files were created.",
            flush=True,
        )
        return

    save_frame(
        raw,
        "insider_transactions.csv",
        "insider_transactions",
    )

    print(
        "Saved insider transaction data.",
        flush=True,
    )

    if signals.empty:
        print(
            "Transactions were collected, but no daily signals "
            "could be generated.",
            flush=True,
        )
        return

    save_frame(
        signals,
        "insider_signals.csv",
        "insider_signals",
    )

    print(
        "Saved insider signal data.",
        flush=True,
    )

    print(
        f"\nTransactions collected: {len(raw)}",
        flush=True,
    )

    print(
        f"Daily signals generated: {len(signals)}",
        flush=True,
    )

    required_columns = {
        "date",
        "insider_factor_score",
        "forward_20d_return",
    }

    if not required_columns.issubset(signals.columns):
        missing = required_columns.difference(signals.columns)

        print(
            "\nBacktest skipped because these columns "
            f"are missing: {sorted(missing)}",
            flush=True,
        )
        return

    usable_signals = signals.dropna(
        subset=[
            "insider_factor_score",
            "forward_20d_return",
        ]
    )

    if usable_signals.empty:
        print(
            "\nBacktest skipped because forward-return data "
            "was unavailable.",
            flush=True,
        )
        return

    information_coefficient_value = information_coefficient(
        usable_signals,
        "insider_factor_score",
        "forward_20d_return",
    )

    print(
        "\nInformation coefficient:",
        information_coefficient_value,
        flush=True,
    )

    backtest = long_short_backtest(
        usable_signals,
        "date",
        "insider_factor_score",
        "forward_20d_return",
    )

    if backtest.empty:
        print(
            "\nBacktest produced no rows. "
            "This is expected with only one ticker or very little data.",
            flush=True,
        )
        print(
            "After the test succeeds, add more tickers and filings.",
            flush=True,
        )
        return

    save_frame(
        backtest,
        "insider_backtest.csv",
        "insider_backtest",
    )

    print(
        "\nSaved insider backtest data.",
        flush=True,
    )

    summary = performance_summary(
        backtest["strategy_return"],
        periods_per_year=12,
    )

    print(
        "\nBacktest performance summary:",
        flush=True,
    )

    print(
        summary,
        flush=True,
    )


if __name__ == "__main__":
    main()
