# Interview talk track

## 30-second version

I built an alternative-data research platform around SEC filings, Form 4 insider transactions, and Reddit sentiment. I designed reusable ingestion, feature-engineering, forward-return, storage, and backtesting modules rather than three disconnected notebooks. The project evaluates factor information coefficients and long-short spreads, includes PostgreSQL, tests, CI, Docker, and a Streamlit dashboard, and explicitly documents biases and production limitations.

## Technical decisions

- Used SEC's structured submissions and filing archives instead of fragile commercial-site scraping.
- Parsed Form 4 transaction XML so grants, sales, and open-market purchases are not conflated.
- Restricted Reddit ticker matching to a defined universe and cashtags to reduce false positives.
- Used merge-as-of logic to align event dates with the next trading session.
- Kept factor formulas transparent before considering more complex machine-learning models.
- Separated research code into modules and scripts so each component is independently testable.

## Limitations to volunteer

- `yfinance` is not point-in-time institutional data.
- Event returns can overlap.
- A static ticker universe creates survivorship and selection bias.
- VADER is not finance-specific.
- Reddit API access and availability can change.
- Results require transaction-cost and neutralization analysis before any economic conclusion.
