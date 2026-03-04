install:
	uv sync

lint:
	uv run ruff check .

format:
	uv run black .

test:
	uv run pytest

local-ci:
	bin/run-local-ci
