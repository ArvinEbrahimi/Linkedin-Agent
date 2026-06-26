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

run-ui:
	streamlit run app/ui/streamlit_app.py --server.port 8501

docker-up:
	docker compose up --build

docker-down:
	docker compose down

e2e:
	python scripts/e2e_smoke.py

e2e-chat:
	python scripts/e2e_smoke.py --chat

extension-icons:
	python scripts/generate_extension_icons.py

clean:
	rm -rf .pytest_cache .ruff_cache dist build *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
