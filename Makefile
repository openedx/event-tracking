export DJANGO_SETTINGS_MODULE=eventtracking.django.tests.settings

MAKE_DOC=make -C doc
SETUP=python setup.py

.PHONY: test.unit style lint

clean:
	$(SETUP) clean
	$(MAKE_DOC) clean
	coverage erase
	find -name '*.pyc' -delete

ci: test.unit test.integration style lint

test.setup:
	pip install -r dev-requirements.txt -q

test: test.unit test.integration test.performance

test.unit: test.setup
	nosetests --cover-erase --with-coverage --cover-branches -A 'not integration and not performance' --cover-min-percentage=95

test.integration: test.setup
	nosetests --verbose --nocapture -a 'integration'

test.performance: test.setup
	nosetests --verbose --nocapture -a 'performance'

style:
	pep8 eventtracking

lint:
	pylint --reports=y eventtracking

install:
	python setup.py install

develop:
	python setup.py develop

doc: doc.html

doc.html:
	$(MAKE_DOC) html

report:
	pep8 eventtracking >pep8.report || true
	pylint -f parseable eventtracking >pylint.report || true
	coverage xml -o coverage.xml
