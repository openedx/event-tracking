export DJANGO_SETTINGS_MODULE=eventtracking.django.tests.settings

MAKE_DOC=make -C doc
SETUP=python setup.py
PYTEST=python -m pytest

.PHONY: lint requirements style test.unit upgrade

help: ## display this help message
	@echo "Please use \`make <target>' where <target> is one of"
	@grep '^[a-zA-Z]' $(MAKEFILE_LIST) | sort | awk -F ':.*?## ' 'NF==2 {printf "\033[36m  %-25s\033[0m %s\n", $$1, $$2}'

clean: ## delete most git-ignored files
	$(SETUP) clean
	$(MAKE_DOC) clean
	coverage erase
	find -name '*.pyc' -delete

ci: test.unit test.integration style lint ## run all tests and quality checks that are used in CI

test.setup: ## install dependencies for running tests
	pip install -r requirements/dev.txt -q

test: test.unit test.integration test.performance ## run all tests

test.unit: test.setup ## run unit tests
	$(PYTEST) --cov-report=html --cov-report term-missing  --cov-branch -k 'not integration and not performance' --cov-fail-under=95 --cov=eventtracking

test.integration: test.setup ## run integration tests
	$(PYTEST) --verbose -s -k 'integration'

test.performance: test.setup ## run performance tests
	$(PYTEST) --verbose -s -k 'performance'

style: ## run pycodestyle on the code
	pycodestyle eventtracking

lint: ## run pylint on the code
	pylint --reports=y eventtracking

install: ## install the event-tracking package locally
	$(SETUP) install

develop:
	$(SETUP) develop

doc: doc.html ## generate the documentation

doc.html:
	$(MAKE_DOC) html

report: ## generate reports for quality checks and code coverage
	pycodestyle eventtracking >pep8.report || true
	pylint -f parseable eventtracking >pylint.report || true
	coverage xml -o coverage.xml

requirements: ## install development environment requirements
	pip install -r requirements/pip.txt
	pip install -r requirements/pip-tools.txt
	pip-sync requirements/dev.txt requirements/private.*

upgrade: export CUSTOM_COMPILE_COMMAND=make upgrade
upgrade: ## update the requirements/*.txt files with the latest packages satisfying requirements/*.in
	pip install -qr requirements/pip-tools.txt
	# Make sure to compile files after any other files they include!
	pip-compile --upgrade --allow-unsafe -o requirements/pip.txt requirements/pip.in
	pip-compile --upgrade -o requirements/pip-tools.txt requirements/pip-tools.in
	pip install -qr requirements/pip.txt
	pip install -qr requirements/pip-tools.txt
	pip-compile --upgrade -o requirements/base.txt requirements/base.in
	pip-compile --upgrade -o requirements/test.txt requirements/test.in
	pip-compile --upgrade -o requirements/ci.txt requirements/ci.in
	pip-compile --upgrade -o requirements/dev.txt requirements/dev.in
	# Let tox control the Django version for tests
	grep -e "^amqp==\|^anyjson==\|^billiard==\|^celery==\|^kombu==\|^click-didyoumean==\|^click-repl==\|^click==\|^prompt-toolkit==\|^vine==" requirements/base.txt  > requirements/celery54.txt
	sed -i.tmp '/^[d|D]jango==/d' requirements/test.txt
	sed -i.tmp '/^djangorestframework==/d' requirements/test.txt
	sed -i.tmp '/^amqp==/d' requirements/test.txt
	sed -i.tmp '/^anyjson==/d' requirements/test.txt
	sed -i.tmp '/^billiard==/d' requirements/test.txt
	sed -i.tmp '/^celery==/d' requirements/test.txt
	sed -i.tmp '/^kombu==/d' requirements/test.txt
	sed -i.tmp '/^click-didyoumean==/d' requirements/test.txt
	sed -i.tmp '/^click-repl==/d' requirements/test.txt
	sed -i.tmp '/^click==/d' requirements/test.txt
	sed -i.tmp '/^click==/d' requirements/test.txt
	sed -i.tmp '/^prompt-toolkit==/d' requirements/test.txt
	sed -i.tmp '/^vine==/d' requirements/test.txt
	rm requirements/test.txt.tmp
