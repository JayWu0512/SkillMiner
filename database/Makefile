.PHONY: install build format lint test clean all
FLAKE8_MAXLINE ?= 105

install:
	pip install --upgrade pip && \
	pip install -r requirements.txt

build:
	python -m src.app.cli

format:
	black src tests scripts

lint:
	flake8 src tests scripts --max-line-length=$(FLAKE8_MAXLINE)

# for local
test:
	pytest -vv --cov=src --cov-report=term-missing tests

# for ci/cd
test-ci:
	pytest -q --cov=src --cov-report=term-missing tests

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .pytest_cache .coverage htmlcov

all: install format lint test clean
