# Developer shortcuts. Run `make help` for the list.
.DEFAULT_GOAL := help
PYTHON ?= python3
IMAGE  ?= planta-filler:local

.PHONY: help install dev lint format test check build clean docker-build docker-login docker-run release-check

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

install: ## Install the package
	$(PYTHON) -m pip install .

dev: ## Install in editable mode with the dev tools
	$(PYTHON) -m pip install -e ".[dev]"

lint: ## Run ruff (lint + format check)
	ruff check src tests
	ruff format --check src tests

format: ## Auto-format and auto-fix with ruff
	ruff check --fix src tests
	ruff format src tests

test: ## Run the test suite
	$(PYTHON) -m pytest

check: lint test ## Lint and test (what CI runs)

build: clean ## Build sdist and wheel into dist/
	$(PYTHON) -m build
	$(PYTHON) -m twine check dist/*

clean: ## Remove build artifacts and caches
	rm -rf build dist src/*.egg-info .pytest_cache .ruff_cache
	find . -name __pycache__ -type d -prune -exec rm -rf {} +

docker-build: ## Build the container image (default tag planta-filler:local, override with IMAGE=...)
	docker build -t $(IMAGE) .

docker-login: ## One-time interactive login to fill the persistent profile volume (needs X11, see docs/docker.md)
	docker run --rm -it -e DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix:ro \
	  -v planta-profile:/home/planta/.selenium_profiles $(IMAGE) --url "$(PLANTA_URL)" --login-only --close-delay 0

docker-run: ## Headless run, e.g. make docker-run PLANTA_URL=https://... ARGS="--strategy random"
	docker run --rm -it -v planta-profile:/home/planta/.selenium_profiles $(IMAGE) \
	  --url "$(PLANTA_URL)" --headless --close-delay 0 $(ARGS)

release-check: ## Verify that the git tag on HEAD matches the package version
	@version=$$($(PYTHON) -c "import sys; sys.path.insert(0, 'src'); import planta_filler; print(planta_filler.__version__)"); \
	tag=$$(git describe --tags --exact-match 2>/dev/null || true); \
	echo "package version: $$version"; echo "tag on HEAD:     $${tag:-<none>}"; \
	if [ "$$tag" != "v$$version" ]; then echo "Tag v$$version is missing on HEAD or does not match."; exit 1; fi; \
	grep -q "## \[$$version\]" CHANGELOG.md || { echo "CHANGELOG.md has no section for $$version"; exit 1; }; \
	echo "OK"
