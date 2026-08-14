# LinkedIn launch post

I recently built **Quant Alternative Data Lab**, a Python research platform for testing whether public alternative data contains information about future equity returns.

The project includes three pipelines:

- SEC earnings-disclosure sentiment from 10-Q and earnings-related 8-K filings
- Form 4 insider-transaction parsing, including open-market purchases and clustered insider activity
- Reddit attention and sentiment signals across a defined stock universe

The platform aligns each signal with forward market returns, evaluates cross-sectional long-short portfolios, and reports information coefficients, Sharpe ratios, cumulative returns, and drawdowns. I also added PostgreSQL support, automated tests, GitHub Actions, Docker, and an interactive Streamlit dashboard.

The biggest lesson was that data collection is only the beginning. The harder parts were defining when a signal was genuinely available, reducing false ticker mentions, separating insider purchases from routine dispositions, and being explicit about backtest biases.

Repository: [ADD GITHUB URL]
Live dashboard: [ADD STREAMLIT URL]

#QuantFinance #DataScience #Python #AlternativeData #FinTech #NLP
