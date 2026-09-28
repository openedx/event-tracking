export DJANGO_SETTINGS_MODULE=eventtracking.django.tests.settings

MAKE_DOC=make -C doc
PYTEST=pytest

.PHONY: lint requirements style test.unit upgrade

help: ## display this help message
	@echo "Please use \`make <target>' where <target> is one of"
	@grep '^[a-zA-Z]' $(MAKEFILE_LIST) | sort | awk -F ':.*?## ' 'NF==2 {printf "\033[36m  %-25s\033[0m %s\n", $$1, $$2}'

clean: ## delete most git-ignored files
	$(MAKE_DOC) clean
	coverage erase
	find -name '*.pyc' -delete

ci: test.unit test.integration style lint ## run all tests and quality checks that are used in CI

test.setup: ## install dependencies for running tests
	uv sync --group dev

test: test.unit test.integration test.performance ## run all tests

test.unit: test.setup ## run unit tests
	$(PYTEST) --cov-report=html --cov-report term-missing  --cov-branch -k 'not integration and not performance' --cov-fail-under=95 --cov=eventtracking

test.integration: test.setup ## run integration tests
	$(PYTEST) --verbose -s -k 'integration'

test.performance: test.setup ## run performance tests
	$(PYTEST) --verbose -s -k 'performance'

style: ## run pycodestyle on the code
	pycodestyle src/eventtracking

lint: ## run pylint on the code
	pylint --reports=y src/eventtracking

install: ## install the event-tracking package locally
	uv pip install .

develop:
	uv pip install -e .

doc: doc.html ## generate the documentation

doc.html:
	$(MAKE_DOC) html

report: ## generate reports for quality checks and code coverage
	pycodestyle src/eventtracking >pep8.report || true
	pylint -f parseable src/eventtracking >pylint.report || true
	coverage xml -o coverage.xml

requirements: ## install development environment requirements
	uv sync --group dev

upgrade: ## update the uv lockfile with the latest packages satisfying pyproject.toml
	uv run --with edx-lint edx_lint write_uv_constraints pyproject.toml
	uv lock --upgrade
