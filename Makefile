PYTHON ?= .venv/bin/python

.PHONY: install test lint format smoke experiments plot web-data web clean

install:
	python3 -m venv .venv
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e ".[dev]"

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check src tests scripts
	$(PYTHON) -m ruff format --check src tests scripts

format:
	$(PYTHON) -m ruff format src tests scripts
	$(PYTHON) -m ruff check --fix src tests scripts

smoke:
	$(PYTHON) -m meshmind.cli smoke-test

experiments:
	$(PYTHON) scripts/run_experiments.py

plot:
	$(PYTHON) -m meshmind.cli plot

web-data:
	$(PYTHON) scripts/export_web_data.py

web:
	npm --prefix web install
	npm --prefix web run dev

clean:
	rm -rf results/*.json results/*.csv results/figures .pytest_cache .ruff_cache
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
