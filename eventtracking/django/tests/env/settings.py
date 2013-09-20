"""A Django settings file for testing"""

from __future__ import absolute_import

from os import path

here = lambda *x: path.join(path.abspath(path.dirname(__file__)), *x)  # pylint: disable=invalid-name

DEBUG = True
TEMPLATE_DEBUG = DEBUG

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'TEST_NAME': ':memory:'
    }
}

TIME_ZONE = 'America/New_York'
USE_TZ = True

SITE_ID = 1

ROOT_URLCONF = 'eventtracking.django.tests.env.urls'
STATIC_ROOT = ''
STATIC_URL = '/static/'

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader'
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
)

INSTALLED_APPS = [
    'django.contrib.staticfiles',
    'django_nose',
    'eventtracking.django'
]

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
