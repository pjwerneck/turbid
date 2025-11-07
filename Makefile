UV := uv
PACKAGE := turbid

help:
	@grep -E '^[a-zA-Z_-]+:.*?#' $(lastword $(MAKEFILE_LIST)) | sed 's/:.*?#/\t- /'

install:  # Sync project dependencies
	$(UV) sync

test:  # Run pytest suite
	$(UV) run pytest -q

test-all:
	@for version in 3.8 3.9 3.10 3.11 3.12 3.13 3.14; do \
        echo "Testing for Python $$version"; \
        uv run --python $$version --isolated --with-editable '.[test]' pytest; \
    done


lint:  # Static checks (ruff)
	$(UV) run ruff check .

format:  # Auto-format (ruff)
	$(UV) run ruff format .

build:  # Build sdist + wheel
	$(UV) build

publish: build  # Publish to PyPI (requires PYPI_TOKEN)
	@if [ -z "$$PYPI_TOKEN" ]; then echo "PYPI_TOKEN not set"; exit 1; fi
	$(UV) publish --token $$PYPI_TOKEN

clean:  # Remove caches and build artifacts
	rm -rf dist build .ruff_cache .pytest_cache .coverage htmlcov

.PHONY: help install test lint format build publish clean