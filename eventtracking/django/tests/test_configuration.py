"""Tests various configuration settings for the django tracker"""

from __future__ import absolute_import

from unittest import TestCase

from django.test.utils import override_settings

from mock import sentinel

from eventtracking import django
from eventtracking import track


TEST_TRACKER_NAME = 'django.test.tracker'


class TestConfiguration(TestCase):
    """Tests various configuration settings for the django tracker"""

    def setUp(self):
        self.tracker = track.get_tracker()

    @override_settings(TRACKING_BACKENDS={
        "fake": {
            'ENGINE': 'eventtracking.django.tests.test_configuration.TrivialFakeBackend'
        }
    })
    def test_configure(self):
        self.configure_tracker()
        fake_backend = self.tracker.get_backend('fake')
        self.assertTrue(isinstance(fake_backend, TrivialFakeBackend))

    def configure_tracker(self, setting_name='TRACKING_BACKENDS'):
        """Reads the tracker configuration from the Django settings"""
        self.tracker = django.DjangoTracker(setting_name)

    @override_settings(TRACKING_BACKENDS={
        "no_engine": {
            'OPTIONS': {}
        }
    })
    def test_ignore_no_engine(self):
        self.configure_tracker()
        with self.assertRaises(KeyError):
            self.tracker.get_backend('no_engine')

    @override_settings(TRACKING_BACKENDS={
        "empty_engine": {
            'ENGINE': ''
        }
    })
    def test_configure_empty_engine(self):
        self.assert_fails_to_configure_with_error()

    def assert_fails_to_configure_with_error(self, error=ValueError):
        """
        Attempts to read the tracker configuration from the Django settings
        and ensures that the tracker construction fails.
        """
        with self.assertRaises(error):
            self.configure_tracker()

    @override_settings(TRACKING_BACKENDS={
        "invalid_package": {
            'ENGINE': 'foo.BarBackend'
        }
    })
    def test_configure_invalid_package(self):
        self.assert_fails_to_configure_with_error()

    @override_settings(TRACKING_BACKENDS={
        "no_package_invalid_class": {
            'ENGINE': 'BarBackend'
        }
    })
    def test_configure_no_package_invalid_class(self):
        self.assert_fails_to_configure_with_error()

    @override_settings(TRACKING_BACKENDS={
        "invalid_class": {
            'ENGINE': 'eventtracking.django.tests.test_configuration.BarBackend'
        }
    })
    def test_configure_invalid_class(self):
        self.assert_fails_to_configure_with_error()

    @override_settings(TRACKING_BACKENDS={
        'with_options': {
            'ENGINE': 'eventtracking.django.tests.test_configuration.FakeBackendWithOptions',
            'OPTIONS': {
                'option': sentinel.option_value
            }
        }
    })
    def test_configure_engine_with_options(self):
        self.configure_tracker()
        self.assertEquals(self.tracker.get_backend('with_options').option, sentinel.option_value)

    @override_settings(TRACKING_BACKENDS={
        'without_options': {
            'ENGINE': 'eventtracking.django.tests.test_configuration.FakeBackendWithOptions'
        }
    })
    def test_configure_engine_missing_options(self):
        self.configure_tracker()
        self.assertEquals(self.tracker.get_backend('without_options').option, None)

    @override_settings(TRACKING_BACKENDS={
        'extra_options': {
            'ENGINE': 'eventtracking.django.tests.test_configuration.FakeBackendWithOptions',
            'OPTIONS': {
                'option': sentinel.option_value,
                'extra_option': sentinel.extra_option_value
            }
        }
    })
    def test_configure_engine_with_extra_options(self):
        self.configure_tracker()
        self.assertEquals(self.tracker.get_backend('extra_options').option, sentinel.option_value)

    @override_settings(TRACKING_BACKENDS={
        'extra_options': {
            'ENGINE': 'eventtracking.django.tests.test_configuration.NotABackend'
        }
    })
    def test_configure_class_not_a_backend(self):
        self.assert_fails_to_configure_with_error()

    @override_settings(MY_TRACKING_BACKENDS={
        'custom_fake': {
            'ENGINE': 'eventtracking.django.tests.test_configuration.TrivialFakeBackend'
        }
    })
    def test_configure_with_custom_settings(self):
        self.configure_tracker('MY_TRACKING_BACKENDS')

        self.assertTrue(self.tracker.get_backend('custom_fake') is not None)

    def test_overrides_default_tracker(self):
        self.assertEquals(id(self.tracker), id(track.get_tracker()))


class TrivialFakeBackend(object):
    """A trivial fake backend without any options"""

    def send(self, event):
        """Don't actually send the event anywhere"""
        pass


class NotABackend(object):
    """A class that is not a backend"""
    pass


class FakeBackendWithOptions(TrivialFakeBackend):
    """A trivial fake backend with options"""

    def __init__(self, **kwargs):
        super(FakeBackendWithOptions, self).__init__()
        self.option = kwargs.get('option', None)
