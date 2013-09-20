export DJANGO_SETTINGS_MODULE=eventtracking.django.tests.settings

.PHONY: test.unit style lint

ci: test.unit test.integration style lint

test.setup:
	pip install -r test-requirements.txt -q

test: test.unit test.integration test.performance

test.unit: test.setup
	nosetests --cover-erase --with-coverage -A 'not integration and not performance' --cover-min-percentage=95

test.integration: test.setup
	nosetests --verbose --nocapture -a 'integration'

test.performance: test.setup
	nosetests --verbose --nocapture -a 'performance'

style:
	pep8

lint:
	pylint --reports=y eventtracking

install:
	python setup.py install
