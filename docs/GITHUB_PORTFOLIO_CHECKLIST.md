# GitHub Portfolio Checklist

## Before the first push

- [ ] Rename `.env.example` copy to `.env` and fill in credentials locally.
- [ ] Confirm `.env` is ignored with `git status`.
- [ ] Replace `YOUR_USERNAME` in README clone commands.
- [ ] Run `ruff check .`.
- [ ] Run `pytest --cov=quantlab`.
- [ ] Run at least one data pipeline.
- [ ] Open the Streamlit dashboard and capture screenshots.
- [ ] Verify no credentials, database passwords, personal tokens, or raw private data are committed.

## Recommended repository settings

- Repository name: `quant-alt-data-lab`
- Description: `SEC and Reddit alternative-data factor research with backtesting and Streamlit`
- Topics: `quant-finance`, `alternative-data`, `python`, `sec-edgar`, `nlp`, `backtesting`, `streamlit`, `postgresql`
- Visibility: Public
- Default branch: `main`
- Enable Issues and Actions

## Strong first release

Create a GitHub release named `v0.1.0` after:

- all tests pass
- the README includes two or more screenshots
- the dashboard runs from a fresh clone
- one sample output snapshot is available

Suggested release notes:

> Initial portfolio release with SEC earnings-disclosure sentiment, Form 4 insider-transaction parsing, Reddit attention signals, forward-return alignment, factor backtests, PostgreSQL support, CI, Docker, and Streamlit visualization.

## Suggested pinned-repository description

> Alternative-data quant research platform using SEC filings, insider transactions, Reddit sentiment, cross-sectional backtesting, and Streamlit.
