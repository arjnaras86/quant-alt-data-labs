from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from quantlab.backtest import information_coefficient, performance_summary
from quantlab.config import settings

st.set_page_config(page_title="Quant Alternative Data Lab", page_icon="📈", layout="wide")
st.title("Quant Alternative Data Lab")
st.caption("Earnings disclosures · insider transactions · Reddit sentiment")

PROJECTS = {
    "Earnings disclosures": {
        "signals": "earnings_signals.csv",
        "backtest": "earnings_backtest.csv",
        "factor": "earnings_factor_score",
        "forward_return": "forward_5d_return",
        "periods": 52,
    },
    "Insider transactions": {
        "signals": "insider_signals.csv",
        "backtest": "insider_backtest.csv",
        "factor": "insider_factor_score",
        "forward_return": "forward_20d_return",
        "periods": 12,
    },
    "Reddit sentiment": {
        "signals": "reddit_signals.csv",
        "backtest": "reddit_backtest.csv",
        "factor": "reddit_factor_score",
        "forward_return": "forward_5d_return",
        "periods": 52,
    },
}


def read_csv(name: str) -> tuple[pd.DataFrame, bool]:
    live_path = settings.processed_dir / name
    if live_path.exists():
        return pd.read_csv(live_path), False
    demo_path = settings.project_root / "data" / "demo" / name
    return (pd.read_csv(demo_path), True) if demo_path.exists() else (pd.DataFrame(), False)


project = st.sidebar.selectbox("Research pipeline", list(PROJECTS))
config = PROJECTS[project]
signals, signals_demo = read_csv(config["signals"])
backtest, backtest_demo = read_csv(config["backtest"])

if signals_demo or backtest_demo:
    st.info("Showing a synthetic demonstration dataset. Run the live pipeline to replace it.")

if signals.empty:
    st.warning(
        f"No output found for {project}. Run the corresponding script locally, then refresh."
    )
    st.code(
        {
            "Earnings disclosures": "python scripts/run_earnings.py",
            "Insider transactions": "python scripts/run_insiders.py",
            "Reddit sentiment": "python scripts/run_reddit.py",
        }[project]
    )
    st.stop()

signals["date"] = pd.to_datetime(signals["date"])

st.sidebar.subheader("Filters")
tickers = sorted(signals["ticker"].dropna().unique())
selected = st.sidebar.multiselect("Tickers", tickers, default=tickers)
date_min = signals["date"].min().date()
date_max = signals["date"].max().date()
date_range = st.sidebar.date_input("Date range", (date_min, date_max))

filtered = signals[signals["ticker"].isin(selected)].copy()
if isinstance(date_range, tuple) and len(date_range) == 2:
    filtered = filtered[
        filtered["date"].between(pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1]))
    ]

ic = information_coefficient(filtered, config["factor"], config["forward_return"])
summary = (
    performance_summary(backtest["strategy_return"], config["periods"])
    if not backtest.empty
    else {}
)

cols = st.columns(4)
cols[0].metric("Signal observations", f"{len(filtered):,}")
cols[1].metric("Spearman IC", "N/A" if pd.isna(ic) else f"{ic:.3f}")
cols[2].metric("Backtest Sharpe", "N/A" if not summary else f"{summary['sharpe']:.2f}")
cols[3].metric(
    "Max drawdown", "N/A" if not summary else f"{summary['max_drawdown']:.1%}"
)

st.subheader("Factor versus forward return")
fig = px.scatter(
    filtered,
    x=config["factor"],
    y=config["forward_return"],
    color="ticker",
    hover_data=["date"],
    trendline="ols" if len(filtered) >= 10 else None,
)
st.plotly_chart(fig, use_container_width=True)

if not backtest.empty:
    backtest["date"] = pd.to_datetime(backtest["date"])
    st.subheader("Long-short equity curve")
    curve = px.line(backtest, x="date", y="equity_curve")
    st.plotly_chart(curve, use_container_width=True)

st.subheader("Signal table")
st.dataframe(filtered.sort_values("date", ascending=False), use_container_width=True)

st.caption(
    "Educational research only. The results are not investment advice and may contain survivorship, "
    "look-ahead, selection, and data-quality biases."
)
