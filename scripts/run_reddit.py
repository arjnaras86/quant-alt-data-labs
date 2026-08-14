from quantlab.backtest import information_coefficient, long_short_backtest, performance_summary
from quantlab.reddit import collect_reddit_signals
from quantlab.storage import save_frame

TICKERS = ["AAPL", "MSFT", "NVDA", "AMD", "TSLA", "PLTR", "SOFI", "META", "GOOGL"]
SUBREDDITS = ["stocks", "investing", "wallstreetbets"]

if __name__ == "__main__":
    raw, signals = collect_reddit_signals(TICKERS, SUBREDDITS, listing="new", limit=250)
    save_frame(raw, "reddit_posts.csv", "reddit_posts")
    save_frame(signals, "reddit_signals.csv", "reddit_signals")
    backtest = long_short_backtest(signals, "date", "reddit_factor_score", "forward_5d_return")
    save_frame(backtest, "reddit_backtest.csv", "reddit_backtest")
    print("Posts:", len(raw), "Signals:", len(signals))
    print("IC:", information_coefficient(signals, "reddit_factor_score", "forward_5d_return"))
    if not backtest.empty:
        print(performance_summary(backtest["strategy_return"], periods_per_year=52))
