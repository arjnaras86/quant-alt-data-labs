from __future__ import annotations

import pandas as pd

def download_adjusted_close(ticker: str, start: str | pd.Timestamp, end: str | pd.Timestamp) -> pd.Series:
    import yfinance as yf

    frame = yf.download(
        ticker,
        start=pd.Timestamp(start).strftime("%Y-%m-%d"),
        end=pd.Timestamp(end).strftime("%Y-%m-%d"),
        auto_adjust=True,
        progress=False,
        threads=False,
    )
    if frame.empty:
        return pd.Series(dtype="float64", name=ticker)

    close = frame["Close"]
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    close.index = pd.to_datetime(close.index).tz_localize(None)
    close.name = ticker
    return close.astype(float)


def add_forward_returns(
    signals: pd.DataFrame,
    ticker_col: str = "ticker",
    date_col: str = "date",
    horizons: tuple[int, ...] = (1, 5, 20),
) -> pd.DataFrame:
    if signals.empty:
        return signals.copy()

    output: list[pd.DataFrame] = []
    work = signals.copy()
    work[date_col] = pd.to_datetime(work[date_col]).dt.normalize()

    for ticker, group in work.groupby(ticker_col, sort=False):
        start = group[date_col].min() - pd.Timedelta(days=10)
        end = group[date_col].max() + pd.Timedelta(days=max(horizons) * 2 + 15)
        close = download_adjusted_close(str(ticker), start, end)
        if close.empty:
            group = group.copy()
            for horizon in horizons:
                group[f"forward_{horizon}d_return"] = pd.NA
            output.append(group)
            continue

        market = close.rename("close").to_frame()
        for horizon in horizons:
            market[f"forward_{horizon}d_return"] = market["close"].shift(-horizon) / market["close"] - 1

        group = group.sort_values(date_col)
        merged = pd.merge_asof(
            group,
            market.reset_index(names=date_col).sort_values(date_col),
            on=date_col,
            direction="forward",
            tolerance=pd.Timedelta(days=4),
        ).drop(columns=["close"])
        output.append(merged)

    return pd.concat(output, ignore_index=True)
