"""A Django settings file for testing"""

from __future__ import absolute_import

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:'
    }
}

SITE_ID = 1

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
)

INSTALLED_APPS = [
    'django_nose',
    'eventtracking.django'
]

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

EVENT_TRACKING_ENABLED = True

SECRET_KEY = "test_key"
