.PHONY: install test test-ci lint clean

install:
	pip install --upgrade pip && \
	pip install -r requirements.txt

# for local development
test:
	pytest -vv --cov=src --cov-report=term-missing tests

# for ci/cd (quiet mode)
test-ci:
	pytest -q --cov=src --cov-report=term-missing tests

lint:
	flake8 src tests --max-line-length=120 --exclude=__pycache__

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .coverage htmlcov .mypy_cache

