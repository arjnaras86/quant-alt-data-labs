# Quant Alternative Data Lab

A portfolio-ready research platform that tests whether public alternative data contains information about subsequent stock returns.

The repository contains three independent pipelines:

1. **Earnings-disclosure sentiment** — retrieves recent SEC 10-Q and earnings-related 8-K filings, engineers tone and uncertainty features, and measures forward returns.
2. **Insider-transaction signals** — parses SEC Form 4 XML, distinguishes open-market purchases from dispositions, constructs insider-cluster features, and runs event-based tests.
3. **Reddit attention and sentiment** — uses Reddit API data to measure ticker attention, discussion intensity, and sentiment, then aligns those signals with future returns.

A shared research layer adds cross-sectional factor backtests, Spearman information coefficients, Sharpe ratio, drawdown, optional PostgreSQL persistence, and a Streamlit dashboard.

> **Disclaimer:** This project is educational research, not investment advice. Backtests can be distorted by look-ahead bias, survivorship bias, selection bias, transaction costs, overlapping returns, and data-quality issues.

## Architecture

```text
SEC EDGAR / Reddit API / market data
                │
                ▼
       collection and parsing
                │
                ▼
        feature engineering
                │
                ▼
      forward-return alignment
                │
                ▼
  IC analysis + long/short backtest
                │
                ▼
     CSV / PostgreSQL / Streamlit
```

## Repository layout

```text
quant-alt-data-lab/
├── app/streamlit_app.py
├── data/
│   ├── raw/
│   └── processed/
├── scripts/
│   ├── run_earnings.py
│   ├── run_insiders.py
│   └── run_reddit.py
├── src/quantlab/
│   ├── backtest.py
│   ├── config.py
│   ├── earnings.py
│   ├── http.py
│   ├── insiders.py
│   ├── market.py
│   ├── reddit.py
│   ├── sec.py
│   ├── sentiment.py
│   └── storage.py
├── tests/
├── .github/workflows/ci.yml
├── .env.example
├── Dockerfile
├── Makefile
└── pyproject.toml
```

## Quick start

### 1. Clone and create an environment

```bash
git clone https://github.com/YOUR_USERNAME/quant-alt-data-lab.git
cd quant-alt-data-lab
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

### 2. Install

```bash
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

### 3. Configure secrets

Copy the example file:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Fill in at minimum:

```env
SEC_USER_AGENT=Your Name your_real_email@example.com
```

For Reddit:

```env
REDDIT_CLIENT_ID=...
REDDIT_CLIENT_SECRET=...
REDDIT_USER_AGENT=quant-alt-data-lab/0.1 by your_reddit_username
```

PostgreSQL is optional:

```env
DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/quant_lab
```

Never commit `.env` or Streamlit secrets.

## Run the projects

```bash
python scripts/run_earnings.py
python scripts/run_insiders.py
python scripts/run_reddit.py
```

Outputs are written to `data/processed/`. If `DATABASE_URL` is configured, the same frames are also written to PostgreSQL.

Launch the dashboard:

```bash
streamlit run app/streamlit_app.py
```

Or use the Makefile:

```bash
make earnings
make insiders
make reddit
make dashboard
```

## Customize the universe

Edit the `TICKERS` constant in each script. Start with a broad universe rather than five stocks; cross-sectional ranking is not meaningful when very few securities share an event date.

Example:

```python
TICKERS = [
    "AAPL", "MSFT", "NVDA", "AMD", "META", "GOOGL",
    "AMZN", "JPM", "GS", "BAC", "XOM", "CVX"
]
```

## Research design

### Earnings-disclosure sentiment

The pipeline retrieves recent `10-Q` and relevant `8-K` filings from SEC EDGAR. It computes:

- VADER compound, positive, negative, and neutral tone
- uncertainty term frequency
- document length
- a transparent composite factor
- 1-, 5-, and 20-trading-day forward returns

The code uses SEC filings rather than scraping commercial transcript publishers. A future extension could plug in a licensed transcript source or FinBERT model behind the same feature interface.

### Insider transactions

The Form 4 pipeline parses non-derivative transactions and extracts:

- reporting owner and officer title
- transaction code
- acquired/disposed indicator
- shares and price per share
- estimated transaction dollar value
- open-market purchase count
- number of distinct insiders buying on the same date
- 5-, 20-, and 60-trading-day forward returns

The factor emphasizes open-market purchases and clustered insider activity. It does **not** assume every Form 4 is bullish.

### Reddit alternative data

The Reddit pipeline collects posts through authenticated API access and computes:

- unique ticker mentions
- breadth across subreddits
- average sentiment and negativity
- total comments and post scores
- a composite attention/sentiment factor
- 1-, 5-, and 20-trading-day forward returns

Ticker detection prioritizes cashtags and restricts ordinary uppercase tokens to a supplied universe to reduce false positives.

## Backtesting methodology

`long_short_backtest` ranks securities on each signal date, buys the top factor quantile, shorts the bottom quantile, and reports an equal-weight spread return. The repository also computes:

- Spearman information coefficient
- cumulative equity curve
- annualized return and volatility
- Sharpe ratio
- maximum drawdown

This is intentionally a research baseline. A stronger version should add:

- point-in-time constituent universes
- explicit signal availability timestamps
- non-overlapping portfolio formation
- delisting returns
- commissions, borrow fees, and slippage
- sector and beta neutralization
- walk-forward validation
- multiple-testing controls

## Tests and continuous integration

```bash
ruff check .
pytest --cov=quantlab
```

GitHub Actions runs both commands for every push and pull request.

## PostgreSQL setup

Create a database:

```sql
CREATE DATABASE quant_lab;
```

Then configure `DATABASE_URL` in `.env`. Tables are replaced on each pipeline run, which is convenient for a portfolio demo. For production, use append/upsert logic and primary keys.

## Docker

```bash
docker build -t quant-alt-data-lab .
docker run --env-file .env -p 8501:8501 quant-alt-data-lab
```

Open `http://localhost:8501`.

## Deploy the dashboard

For Streamlit Community Cloud:

1. Push this repository to GitHub.
2. Create a new Streamlit app from the repository.
3. Set the entry point to `app/streamlit_app.py`.
4. Add required values in the app's Secrets settings rather than committing `.env`.
5. The dashboard needs generated CSVs in `data/processed/`. For a public demo, either commit a small sanitized snapshot or add a scheduled data job that writes outputs to durable storage.

A simple public portfolio deployment should use a small, dated demonstration dataset and clearly label it as a snapshot. Do not expose Reddit or database credentials.

## Suggested screenshots for the GitHub page

After generating data and launching Streamlit, capture:

1. project selector and KPI cards
2. factor-versus-return scatter plot
3. long-short equity curve
4. sample Form 4 transaction table

Store images under `docs/images/` and add them to this README.

## Resume bullet

> Built a Python alternative-data research platform that ingests SEC filings and Reddit activity, engineers NLP and insider-trading factors, aligns signals with forward market returns, and evaluates cross-sectional long-short strategies through information coefficients, Sharpe ratios, drawdowns, PostgreSQL, CI tests, and a Streamlit dashboard.

## Future improvements

- FinBERT and sentence-level management tone
- market- and sector-adjusted abnormal returns
- point-in-time S&P 500 membership
- event-study confidence intervals
- Airflow or Prefect orchestration
- object storage for raw filings
- incremental database upserts
- portfolio constraints and turnover analysis
- experiment tracking with MLflow

## Data and access notes

- SEC requests use a declared User-Agent, retry behavior, and a conservative client-side rate limit.
- Reddit access requires credentials and remains subject to Reddit's current developer terms and platform policies.
- Market prices are downloaded with `yfinance`, an unofficial convenience library. For production or audited research, replace it with a licensed point-in-time market-data provider.

## License

MIT
