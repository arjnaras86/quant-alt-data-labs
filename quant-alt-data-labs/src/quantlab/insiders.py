from __future__ import annotations

from decimal import Decimal, InvalidOperation

import numpy as np
import pandas as pd

from quantlab.market import add_forward_returns
from quantlab.sec import Filing, SecClient


def _decimal(text: str | None) -> float | None:
    """
    Convert SEC numeric text into a Python float.

    Returns None when the value is missing or cannot be converted.
    """
    try:
        cleaned = (text or "").replace(",", "").strip()

        if not cleaned:
            return None

        return float(Decimal(cleaned))

    except (InvalidOperation, ValueError):
        return None


def parse_form4(client: SecClient, filing: Filing) -> list[dict]:
    """
    Download and parse one SEC Form 4 filing.

    Extracts non-derivative insider transactions such as open-market
    purchases and sales.
    """
    soup = client.filing_xml(filing)

    owner = soup.find("reportingOwner")

    owner_name_node = owner.find("rptOwnerName") if owner else None
    owner_name = (
        owner_name_node.get_text(strip=True)
        if owner_name_node
        else None
    )

    officer_title_node = soup.find("officerTitle")
    officer_title = (
        officer_title_node.get_text(strip=True)
        if officer_title_node
        else None
    )

    rows: list[dict] = []

    for transaction in soup.find_all("nonDerivativeTransaction"):
        code_node = transaction.find("transactionCode")
        shares_node = transaction.find("transactionShares")
        price_node = transaction.find("transactionPricePerShare")
        acquired_node = transaction.find(
            "transactionAcquiredDisposedCode"
        )
        date_node = transaction.find("transactionDate")

        transaction_code = (
            code_node.value.get_text(strip=True)
            if code_node and code_node.value
            else None
        )

        shares = (
            _decimal(shares_node.value.get_text(strip=True))
            if shares_node and shares_node.value
            else None
        )

        price_per_share = (
            _decimal(price_node.value.get_text(strip=True))
            if price_node and price_node.value
            else None
        )

        acquired_disposed = (
            acquired_node.value.get_text(strip=True)
            if acquired_node and acquired_node.value
            else None
        )

        transaction_date = (
            date_node.value.get_text(strip=True)
            if date_node and date_node.value
            else filing.report_date
        )

        dollar_value = (
            shares * price_per_share
            if shares is not None and price_per_share is not None
            else None
        )

        rows.append(
            {
                "ticker": filing.ticker,
                "date": transaction_date,
                "filing_date": filing.filing_date,
                "accession_number": filing.accession_number,
                "owner_name": owner_name,
                "officer_title": officer_title,
                "transaction_code": transaction_code,
                "acquired_disposed": acquired_disposed,
                "shares": shares,
                "price_per_share": price_per_share,
                "dollar_value": dollar_value,
                "source_url": filing.document_url,
            }
        )

    return rows


def collect_insider_signals(
    tickers: list[str],
    filings_per_ticker: int = 40,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Collect recent Form 4 transactions and create daily insider signals.

    Parameters
    ----------
    tickers:
        Stock tickers to analyze.

    filings_per_ticker:
        Maximum number of recent Form 4 filings downloaded for each ticker.

    Returns
    -------
    raw:
        Individual insider transactions.

    signals:
        Daily ticker-level insider factors with forward returns.
    """
    client = SecClient()
    transactions: list[dict] = []

    for ticker in tickers:
        print(
            f"\nLoading recent Form 4 filings for {ticker}...",
            flush=True,
        )

        try:
            filings = client.recent_filings(
                ticker,
                forms=("4",),
                limit=filings_per_ticker,
            )

        except Exception as error:
            print(
                f"Could not retrieve filings for {ticker}: {error}",
                flush=True,
            )
            continue

        print(
            f"Found {len(filings)} filings for {ticker}.",
            flush=True,
        )

        for filing_number, filing in enumerate(filings, start=1):
            print(
                f"  Parsing filing "
                f"{filing_number}/{len(filings)}: "
                f"{filing.accession_number}",
                flush=True,
            )

            try:
                parsed_transactions = parse_form4(client, filing)
                transactions.extend(parsed_transactions)

                print(
                    f"    Extracted "
                    f"{len(parsed_transactions)} transactions.",
                    flush=True,
                )

            except Exception as error:
                print(
                    f"    Skipped filing because of error: {error}",
                    flush=True,
                )

    raw = pd.DataFrame(transactions)

    if raw.empty:
        print(
            "\nNo insider transactions were extracted.",
            flush=True,
        )
        return raw, pd.DataFrame()

    raw["date"] = pd.to_datetime(
        raw["date"],
        errors="coerce",
    )

    raw["filing_date"] = pd.to_datetime(
        raw["filing_date"],
        errors="coerce",
    )

    raw = raw.dropna(subset=["ticker", "date"])

    raw["signed_dollar_value"] = (
        raw["dollar_value"]
        .fillna(0.0)
        .astype(float)
    )

    raw.loc[
        raw["acquired_disposed"] == "D",
        "signed_dollar_value",
    ] *= -1

    raw["is_open_market_purchase"] = (
        (raw["transaction_code"] == "P")
        & (raw["acquired_disposed"] == "A")
    )

    raw["is_open_market_sale"] = (
        (raw["transaction_code"] == "S")
        & (raw["acquired_disposed"] == "D")
    )

    signals = (
        raw.groupby(
            ["ticker", "date"],
            as_index=False,
        )
        .agg(
            transaction_count=(
                "accession_number",
                "count",
            ),
            distinct_insiders=(
                "owner_name",
                "nunique",
            ),
            net_dollar_value=(
                "signed_dollar_value",
                "sum",
            ),
            purchase_count=(
                "is_open_market_purchase",
                "sum",
            ),
            sale_count=(
                "is_open_market_sale",
                "sum",
            ),
        )
    )

    signals["insider_factor_score"] = (
        np.log1p(
            signals["net_dollar_value"].clip(lower=0)
        )
        + 0.75 * signals["purchase_count"]
        + 0.25 * signals["distinct_insiders"]
        - 0.25 * signals["sale_count"]
    )

    print(
        "\nAdding stock-price forward returns...",
        flush=True,
    )

    try:
        signals = add_forward_returns(
            signals,
            horizons=(5, 20, 60),
        )

    except Exception as error:
        print(
            f"Could not add forward returns: {error}",
            flush=True,
        )

    return raw, signals