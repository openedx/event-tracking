"""
Test the event tracking module
"""
from __future__ import absolute_import

from datetime import datetime
from unittest import TestCase

from mock import MagicMock
from mock import patch
from mock import sentinel

from eventtracking import track
from eventtracking.backends import BaseBackend


class TestTrack(TestCase):  # pylint: disable=missing-docstring

    def setUp(self):
        # Ensure all backends are removed after executing
        self.addCleanup(track.configure, {})

        self._mock_backends = []
        self._mock_backend = None
        self.configure_mock_backends(1)

        self._expected_timestamp = datetime.utcnow()
        self._datetime_patcher = patch('eventtracking.track.datetime')
        self.addCleanup(self._datetime_patcher.stop)
        mock_datetime = self._datetime_patcher.start()
        mock_datetime.utcnow.return_value = self._expected_timestamp  # pylint: disable=maybe-no-member

    def configure_mock_backends(self, number_of_mocks):
        """Ensure the tracking module has the requisite number of mock backends"""
        config = {}
        for i in range(number_of_mocks):
            name = 'mock{0}'.format(i)
            config[name] = {
                'ENGINE': 'eventtracking.tests.test_track.TrivialFakeBackend'
            }

        track.configure(config)

        self._mock_backends = []
        for i in range(number_of_mocks):
            backend = self.get_mock_backend(i)
            backend.send = MagicMock()
            self._mock_backends.append(backend)
        self._mock_backend = self._mock_backends[0]

    def get_mock_backend(self, index):
        """Get the mock backend created by `configure_mock_backends`"""
        return track.BACKENDS['mock{0}'.format(index)]

    def test_event_simple_event_without_data(self):
        track.event(sentinel.event_type)

        self.assert_backend_called_with(sentinel.event_type)

    def assert_backend_called_with(self, event_type, data=None, backend=None):
        """Ensures the backend is called exactly once with the expected data."""
        if not backend:
            backend = self._mock_backend

        backend.send.assert_called_once_with(
            {
                'event_type': event_type,
                'timestamp': self._expected_timestamp,
                'data': data or {}
            }
        )

    def test_event_simple_event_with_data(self):
        track.event(
            sentinel.event_type,
            {
                sentinel.key: sentinel.value
            }
        )

        self.assert_backend_called_with(
            sentinel.event_type,
            {
                sentinel.key: sentinel.value
            }
        )

    def test_multiple_backends(self):
        self.configure_mock_backends(2)
        track.event(sentinel.event_type)

        for backend in self._mock_backends:
            self.assert_backend_called_with(
                sentinel.event_type, backend=backend)

    def test_single_backend_failure(self):
        self.configure_mock_backends(2)
        self.get_mock_backend(0).send.side_effect = Exception

        track.event(sentinel.event_type)

        self.assert_backend_called_with(
            sentinel.event_type, backend=self.get_mock_backend(1))

    def test_configure(self):
        track.configure({
            "fake": {
                'ENGINE': 'eventtracking.tests.test_track.TrivialFakeBackend'
            }
        })
        fake_backend = track.BACKENDS['fake']
        self.assertTrue(isinstance(fake_backend, TrivialFakeBackend))

    def test_ignore_no_engine(self):
        track.configure({
            "no_engine": {
                'OPTIONS': {}
            }
        })
        self.assertEquals(len(track.BACKENDS), 0)

    def test_configure_empty_engine(self):
        try:
            track.configure({
                "empty_engine": {
                    'ENGINE': ''
                }
            })
            self.fail('Expected exception to be thrown when attempting to add a backend with an empty engine')
        except ValueError:
            pass

    def test_configure_invalid_package(self):
        try:
            track.configure({
                "invalid_package": {
                    'ENGINE': 'foo.BarBackend'
                }
            })
            self.fail('Expected exception to be thrown when attempting to add a backend from a non-existent package')
        except ValueError:
            pass

    def test_configure_no_package_invalid_class(self):
        try:
            track.configure({
                "no_package_invalid_class": {
                    'ENGINE': 'BarBackend'
                }
            })
            self.fail('Expected exception to be thrown when attempting to add a non-existent backend class')
        except ValueError:
            pass

    def test_configure_invalid_class(self):
        try:
            track.configure({
                "invalid_class": {
                    'ENGINE': 'eventtracking.tests.test_track.BarBackend'
                }
            })
            self.fail('Expected exception to be thrown when attempting to add a non-existent backend class')
        except ValueError:
            pass

    def test_configure_engine_not_a_backend(self):
        try:
            track.configure({
                "not_a_backend": {
                    'ENGINE': 'eventtracking.tests.test_track.NotABackend'
                }
            })
            self.fail(
                'Expected exception to be thrown when attempting to add a backend class that'
                ' does not subclass BaseBackend'
            )
        except ValueError:
            pass

    def test_configure_engine_with_options(self):
        track.configure({
            'with_options': {
                'ENGINE': 'eventtracking.tests.test_track.FakeBackendWithOptions',
                'OPTIONS': {
                    'option': sentinel.option_value
                }
            }
        })
        self.assertEquals(track.BACKENDS['with_options'].option, sentinel.option_value)

    def test_configure_engine_missing_options(self):
        track.configure({
            'without_options': {
                'ENGINE': 'eventtracking.tests.test_track.FakeBackendWithOptions'
            }
        })
        self.assertEquals(track.BACKENDS['without_options'].option, None)

    def test_configure_engine_with_extra_options(self):
        track.configure({
            'extra_options': {
                'ENGINE': 'eventtracking.tests.test_track.FakeBackendWithOptions',
                'OPTIONS': {
                    'option': sentinel.option_value,
                    'extra_option': sentinel.extra_option_value
                }
            }
        })
        self.assertEquals(track.BACKENDS['extra_options'].option, sentinel.option_value)


class TrivialFakeBackend(BaseBackend):
    """A trivial fake backend without any options"""

    def send(self, event):
        pass


class NotABackend(object):
    """
    A class that is not a backend
    """
    pass


class FakeBackendWithOptions(BaseBackend):
    """A trivial fake backend with options"""

    def __init__(self, **kwargs):
        super(FakeBackendWithOptions, self).__init__()
        self.option = kwargs.get('option', None)

    def send(self, event):
        pass
