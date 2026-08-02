.PHONY: install test lint earnings insiders reddit dashboard
install:
	python -m pip install -e ".[dev]"
test:
	pytest --cov=quantlab
lint:
	ruff check .
earnings:
	python scripts/run_earnings.py
insiders:
	python scripts/run_insiders.py
reddit:
	python scripts/run_reddit.py
dashboard:
	streamlit run app/streamlit_app.py
