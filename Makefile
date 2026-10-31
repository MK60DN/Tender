.PHONY: install test run lint verify

install:
	python -m pip install -r requirements-dev.txt

test:
	python agent_layer/tests/run_all.py

run:
	cd agent_layer && python -m uvicorn app.main:app --host 127.0.0.1 --port 8080

lint:
	ruff check agent_layer

verify:
	python scripts/verify_repository.py
	python agent_layer/tests/run_all.py
