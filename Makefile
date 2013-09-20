TEST_WITH_COVERAGE=nosetests --cover-erase --with-coverage
export DJANGO_SETTINGS_MODULE=eventtracking.django.tests.env.settings

ci: test style lint

test.setup:
	pip install -r test-requirements.txt -q

test: test.unit test.integration

test.unit: test.setup
	$(TEST_WITH_COVERAGE) -A 'not integration and not performance' --cover-min-percentage=95

test.integration: test.setup
	$(TEST_WITH_COVERAGE) -a 'integration'

test.performance: test.setup
	nosetests --verbose --nocapture -a 'performance'

style:
	pep8

lint:
	pylint --reports=y eventtracking

install:
	python setup.py install
