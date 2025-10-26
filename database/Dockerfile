# syntax=docker/dockerfile:1
FROM python:3.11-slim AS base

# Optional: faster, cleaner installs
ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

# copy project
COPY src /app/src
COPY tests /app/tests
COPY scripts /app/scripts
COPY data/test /app/data/test

# default: run test
CMD ["pytest", "-q", "--cov=src", "--cov-report=term-missing", "tests"]
