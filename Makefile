.PHONY: install install-dev lint format test run clean

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

lint:
	ruff check app tests

format:
	ruff check --fix app tests
	ruff format app tests

test:
	pytest -v

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

clean:
	rm -rf .pytest_cache .ruff_cache dist build *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
