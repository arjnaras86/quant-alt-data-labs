from __future__ import annotations

import numpy as np
import pandas as pd
import requests

from quantlab.market import add_forward_returns
from quantlab.sec import SecClient
from quantlab.sentiment import score_text


def collect_earnings_disclosure_signals(
    tickers: list[str],
    filings_per_ticker: int = 3,
) -> pd.DataFrame:
    """
    Collect recent earnings-related SEC disclosures and calculate
    sentiment-based signals.

    Network or parsing failures are logged and skipped so one filing
    does not stop the entire pipeline.
    """
    client = SecClient()
    rows: list[dict] = []

    for ticker in tickers:
        print(
            f"\nLoading earnings disclosures for {ticker}...",
            flush=True,
        )

        try:
            filings = client.recent_filings(
                ticker,
                forms=("10-Q", "8-K"),
                limit=filings_per_ticker,
            )

        except Exception as error:
            print(
                f"Could not retrieve filing list for {ticker}: {error}",
                flush=True,
            )
            continue

        print(
            f"Found {len(filings)} candidate filings for {ticker}.",
            flush=True,
        )

        for filing_number, filing in enumerate(filings, start=1):
            print(
                f"  Downloading filing "
                f"{filing_number}/{len(filings)}: "
                f"{filing.accession_number}",
                flush=True,
            )

            try:
                text = client.filing_text(filing)

            except requests.exceptions.Timeout:
                print(
                    "    SEC request timed out. Skipping filing.",
                    flush=True,
                )
                continue

            except requests.exceptions.RequestException as error:
                print(
                    f"    SEC request failed: {error}",
                    flush=True,
                )
                continue

            except Exception as error:
                print(
                    f"    Could not parse filing: {error}",
                    flush=True,
                )
                continue

            if not text or len(text.strip()) < 500:
                print(
                    "    Filing text was empty or too short. Skipping.",
                    flush=True,
                )
                continue

            print(
                f"    Scoring {len(text):,} characters...",
                flush=True,
            )

            try:
                features = score_text(text)

            except Exception as error:
                print(
                    f"    Sentiment scoring failed: {error}",
                    flush=True,
                )
                continue

            rows.append(
                {
                    "ticker": filing.ticker,
                    "date": filing.filing_date,
                    "report_date": filing.report_date,
                    "form": filing.form,
                    "accession_number": filing.accession_number,
                    "source_url": filing.document_url,
                    **features,
                }
            )

            print(
                "    Filing completed.",
                flush=True,
            )

    signals = pd.DataFrame(rows)

    if signals.empty:
        print(
            "\nNo earnings disclosures were successfully processed.",
            flush=True,
        )
        return signals

    signals["date"] = pd.to_datetime(
        signals["date"],
        errors="coerce",
    )

    signals["report_date"] = pd.to_datetime(
        signals["report_date"],
        errors="coerce",
    )

    signals = signals.dropna(
        subset=["ticker", "date"],
    )

    signals["earnings_factor_score"] = (
        signals["compound_sentiment"]
        - 3.0 * signals["negative"]
        - 10.0 * signals["uncertainty_rate"]
        + 0.25 * signals["positive"]
    )

    print(
        "\nAdding forward stock returns...",
        flush=True,
    )

    try:
        signals = add_forward_returns(
            signals,
            horizons=(1, 5, 20),
        )

    except Exception as error:
        print(
            f"Could not add forward returns: {error}",
            flush=True,
        )

    return signals