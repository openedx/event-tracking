"""A Django settings file for testing"""


DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:'
    }
}

SITE_ID = 1

MIDDLEWARE = (
    'django.middleware.common.CommonMiddleware',
)

INSTALLED_APPS = [
    'eventtracking.django'
]

EVENT_TRACKING_ENABLED = True

SECRET_KEY = "test_key"
