import pandas as pd

from quantlab.backtest import long_short_backtest, performance_summary


def test_long_short_backtest_constructs_spread():
    df = pd.DataFrame(
        {
            "date": ["2026-01-01"] * 5,
            "ticker": list("ABCDE"),
            "factor": [1, 2, 3, 4, 5],
            "future": [-0.02, -0.01, 0.00, 0.02, 0.04],
        }
    )
    result = long_short_backtest(df, "date", "factor", "future", quantile=0.2)
    assert len(result) == 1
    assert result.iloc[0]["strategy_return"] == 0.06


def test_performance_summary_has_core_metrics():
    summary = performance_summary(pd.Series([0.01, -0.005, 0.02]), periods_per_year=12)
    assert set(summary) == {
        "total_return",
        "annualized_return",
        "annualized_volatility",
        "sharpe",
        "max_drawdown",
    }
