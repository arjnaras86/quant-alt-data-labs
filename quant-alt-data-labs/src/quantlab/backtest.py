from __future__ import annotations

import numpy as np
import pandas as pd


def information_coefficient(df: pd.DataFrame, factor_col: str, return_col: str) -> float:
    clean = df[[factor_col, return_col]].dropna()
    if len(clean) < 3:
        return float("nan")
    return float(clean[factor_col].corr(clean[return_col], method="spearman"))


def long_short_backtest(
    df: pd.DataFrame,
    date_col: str,
    factor_col: str,
    return_col: str,
    quantile: float = 0.2,
    minimum_assets: int = 5,
) -> pd.DataFrame:
    rows: list[dict[str, float | pd.Timestamp | int]] = []
    work = df.copy()
    work[date_col] = pd.to_datetime(work[date_col])

    for date, group in work.groupby(date_col):
        group = group.dropna(subset=[factor_col, return_col]).copy()
        if len(group) < minimum_assets:
            continue
        low = group[factor_col].quantile(quantile)
        high = group[factor_col].quantile(1 - quantile)
        longs = group[group[factor_col] >= high]
        shorts = group[group[factor_col] <= low]
        if longs.empty or shorts.empty:
            continue
        rows.append(
            {
                "date": date,
                "asset_count": len(group),
                "long_count": len(longs),
                "short_count": len(shorts),
                "long_return": longs[return_col].mean(),
                "short_return": shorts[return_col].mean(),
                "strategy_return": longs[return_col].mean() - shorts[return_col].mean(),
            }
        )

    result = pd.DataFrame(rows)
    if not result.empty:
        result = result.sort_values("date")
        result["equity_curve"] = (1 + result["strategy_return"]).cumprod()
    return result


def performance_summary(returns: pd.Series, periods_per_year: float = 252.0) -> dict[str, float]:
    clean = pd.to_numeric(returns, errors="coerce").dropna()
    if clean.empty:
        return {key: float("nan") for key in ("total_return", "annualized_return", "annualized_volatility", "sharpe", "max_drawdown")}

    equity = (1 + clean).cumprod()
    total_return = equity.iloc[-1] - 1
    years = len(clean) / periods_per_year
    annualized_return = equity.iloc[-1] ** (1 / years) - 1 if years > 0 else float("nan")
    annualized_volatility = clean.std(ddof=1) * np.sqrt(periods_per_year)
    sharpe = clean.mean() / clean.std(ddof=1) * np.sqrt(periods_per_year) if clean.std(ddof=1) else float("nan")
    drawdown = equity / equity.cummax() - 1
    return {
        "total_return": float(total_return),
        "annualized_return": float(annualized_return),
        "annualized_volatility": float(annualized_volatility),
        "sharpe": float(sharpe),
        "max_drawdown": float(drawdown.min()),
    }
