"""Tests various configuration settings for the django tracker"""


from unittest import TestCase

from unittest.mock import sentinel
from django.test.utils import override_settings

from eventtracking import tracker
from eventtracking.django.django_tracker import DjangoTracker, override_default_tracker


TEST_TRACKER_NAME = 'django.test.tracker'


class TestConfiguration(TestCase):
    """Tests various configuration settings for the django tracker"""

    def setUp(self):
        super().setUp()
        override_default_tracker()
        self.tracker = tracker.get_tracker()

    @override_settings(EVENT_TRACKING_BACKENDS={
        "fake": {
            'ENGINE': 'eventtracking.django.tests.test_configuration.TrivialFakeBackend'
        }
    })
    def test_configure(self):
        self.configure_tracker()
        fake_backend = self.tracker.get_backend('fake')
        self.assertTrue(isinstance(fake_backend, TrivialFakeBackend))

    def configure_tracker(self):
        """Reads the tracker configuration from the Django settings"""
        self.tracker = DjangoTracker()

    @override_settings(EVENT_TRACKING_BACKENDS={
        "no_engine": {
            'OPTIONS': {}
        }
    })
    def test_ignore_no_engine(self):
        with self.assertRaises(ValueError):
            self.configure_tracker()

    @override_settings(EVENT_TRACKING_BACKENDS={
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

    @override_settings(EVENT_TRACKING_BACKENDS={
        "invalid_package": {
            'ENGINE': 'foo.BarBackend'
        }
    })
    def test_configure_invalid_package(self):
        self.assert_fails_to_configure_with_error()

    @override_settings(EVENT_TRACKING_BACKENDS={
        "no_package_invalid_class": {
            'ENGINE': 'BarBackend'
        }
    })
    def test_configure_no_package_invalid_class(self):
        self.assert_fails_to_configure_with_error()

    @override_settings(EVENT_TRACKING_BACKENDS={
        "invalid_class": {
            'ENGINE': 'eventtracking.django.tests.test_configuration.BarBackend'
        }
    })
    def test_configure_invalid_class(self):
        self.assert_fails_to_configure_with_error()

    @override_settings(EVENT_TRACKING_BACKENDS={
        'with_options': {
            'ENGINE': 'eventtracking.django.tests.test_configuration.FakeBackendWithOptions',
            'OPTIONS': {
                'option': sentinel.option_value
            }
        }
    })
    def test_configure_engine_with_options(self):
        self.configure_tracker()
        self.assertEqual(self.tracker.get_backend('with_options').option, sentinel.option_value)

    @override_settings(EVENT_TRACKING_BACKENDS={
        'without_options': {
            'ENGINE': 'eventtracking.django.tests.test_configuration.FakeBackendWithOptions'
        }
    })
    def test_configure_engine_missing_options(self):
        self.configure_tracker()
        self.assertEqual(self.tracker.get_backend('without_options').option, None)

    @override_settings(EVENT_TRACKING_BACKENDS={
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
        self.assertEqual(self.tracker.get_backend('extra_options').option, sentinel.option_value)

    @override_settings(EVENT_TRACKING_BACKENDS={
        'extra_options': {
            'ENGINE': 'eventtracking.django.tests.test_configuration.NotABackend'
        }
    })
    def test_configure_class_not_a_backend(self):
        self.assert_fails_to_configure_with_error()

    @override_settings(EVENT_TRACKING_BACKENDS={
        'outer_backend': {
            'ENGINE': 'eventtracking.django.tests.test_configuration.NestedBackend',
            'OPTIONS': {
                'backends': {
                    'inner_backend': {
                        'ENGINE': 'eventtracking.django.tests.test_configuration.FakeBackendWithOptions',
                        'OPTIONS': {
                            'option': sentinel.option_value,
                            'extra_option': sentinel.extra_option_value
                        }
                    },
                    'nested_backend': {
                        'ENGINE': 'eventtracking.django.tests.test_configuration.NestedBackend',
                        'OPTIONS': {
                            'backends': {
                                'trivial': {
                                    'ENGINE': 'eventtracking.django.tests.test_configuration.TrivialFakeBackend'
                                }
                            },
                            'processors': [
                                {'ENGINE': 'eventtracking.django.tests.test_configuration.NopProcessor'},
                            ]
                        }
                    }
                },
                'processors': [
                    {'ENGINE': 'eventtracking.django.tests.test_configuration.NopProcessor'},
                    {'ENGINE': 'eventtracking.django.tests.test_configuration.NopProcessor'},
                ]
            }
        }
    })
    def test_configure_nested_backends(self):
        self.configure_tracker()
        outer_backend = self.tracker.get_backend('outer_backend')
        self.assertEqual(len(outer_backend.backends), 2)

        inner_backend = outer_backend.backends['inner_backend']
        self.assertEqual(inner_backend.option, sentinel.option_value)

        self.assertEqual(len(outer_backend.processors), 2)
        self.assertTrue(isinstance(outer_backend.processors[0], NopProcessor))
        self.assertTrue(isinstance(outer_backend.processors[1], NopProcessor))

        nested_backend = outer_backend.backends['nested_backend']
        self.assertEqual(len(nested_backend.backends), 1)
        self.assertTrue(isinstance(nested_backend.backends['trivial'], TrivialFakeBackend))
        self.assertTrue(isinstance(nested_backend.processors[0], NopProcessor))

    @override_settings(EVENT_TRACKING_ENABLED=True)
    def test_overrides_default_tracker(self):
        override_default_tracker()
        self.assertTrue(isinstance(tracker.get_tracker(), DjangoTracker))

    @override_settings(EVENT_TRACKING_ENABLED=False)
    def test_leaves_default_tracker_alone(self):
        override_default_tracker()
        self.assertTrue(isinstance(tracker.get_tracker(), tracker.Tracker))

    @override_settings(EVENT_TRACKING_PROCESSORS=[
        {
            'ENGINE': 'eventtracking.django.tests.test_configuration.NopProcessor'
        }
    ])
    def test_single_processor(self):
        self.configure_tracker()
        self.assertEqual(len(self.tracker.processors), 1)
        self.assertTrue(isinstance(self.tracker.processors[0], NopProcessor))

    @override_settings(EVENT_TRACKING_PROCESSORS=[
        {
            'ENGINE': 'eventtracking.django.tests.test_configuration.ProcessorWithOptions',
            'OPTIONS': {
                'option': sentinel.option_value
            }
        }
    ])
    def test_processor_with_options(self):
        self.configure_tracker()
        self.assertEqual(len(self.tracker.processors), 1)
        self.assertTrue(isinstance(self.tracker.processors[0], ProcessorWithOptions))
        self.assertEqual(self.tracker.processors[0].option, sentinel.option_value)

    @override_settings(EVENT_TRACKING_PROCESSORS=[
        {}
    ])
    def test_missing_processor_engine(self):
        with self.assertRaises(ValueError):
            self.configure_tracker()

    @override_settings(EVENT_TRACKING_PROCESSORS=[
        {
            'ENGINE': 'eventtracking.django.tests.test_configuration.NopProcessor'
        },
        {
            'ENGINE': 'eventtracking.django.tests.test_configuration.NopProcessor'
        }
    ])
    def test_multiple_processor(self):
        self.configure_tracker()
        self.assertEqual(len(self.tracker.processors), 2)
        self.assertTrue(isinstance(self.tracker.processors[0], NopProcessor))
        self.assertTrue(isinstance(self.tracker.processors[1], NopProcessor))


class TrivialFakeBackend:
    """A trivial fake backend without any options"""

    def send(self, event):
        """Don't actually send the event anywhere"""


class NotABackend:
    """A class that is not a backend"""


class FakeBackendWithOptions(TrivialFakeBackend):
    """A trivial fake backend with options"""

    def __init__(self, **kwargs):
        super().__init__()
        self.option = kwargs.get('option', None)


class NopProcessor:
    """Changes every event"""

    def __call__(self, event):
        pass


class ProcessorWithOptions:
    """Takes in an argument"""

    def __init__(self, **kwargs):
        self. option = kwargs.get('option', None)

    def __call__(self, event):
        pass


class NestedBackend(TrivialFakeBackend):
    """Supports other backends as children"""

    def __init__(self, backends=None, processors=None, **_kwargs):
        self.backends = backends or {}
        self.processors = processors or []
