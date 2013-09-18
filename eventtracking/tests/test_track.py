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


class TestTrack(TestCase):  # pylint: disable=missing-docstring

    def setUp(self):
        self._mock_backend = MagicMock()
        self.addCleanup(track.BACKENDS.remove, self._mock_backend)
        track.BACKENDS.append(self._mock_backend)

        self._expected_timestamp = datetime.utcnow()
        self._datetime_patcher = patch('eventtracking.track.datetime')
        self.addCleanup(self._datetime_patcher.stop)
        mock_datetime = self._datetime_patcher.start()
        mock_datetime.utcnow.return_value = self._expected_timestamp  # pylint: disable=maybe-no-member

    def test_event_simple_event_without_data(self):
        track.event(sentinel.event_type)

        self.assert_backend_called_with(sentinel.event_type)

    def assert_backend_called_with(self, event_type, data=None, backend=None):
        """Ensures the backend is called exactly once with the expected data."""
        if not backend:
            backend = self._mock_backend

        backend.event.assert_called_once_with(
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
        another_backend = MagicMock()
        track.BACKENDS.append(another_backend)
        try:
            track.event(sentinel.event_type)

            self.assert_backend_called_with(sentinel.event_type)
            self.assert_backend_called_with(
                sentinel.event_type, backend=another_backend)
        finally:
            track.BACKENDS.remove(another_backend)

    def test_single_backend_failure(self):
        self._mock_backend.event.side_effect = Exception

        another_backend = MagicMock()
        track.BACKENDS.append(another_backend)
        try:
            track.event(sentinel.event_type)

            self.assert_backend_called_with(
                sentinel.event_type, backend=another_backend)
        finally:
            track.BACKENDS.remove(another_backend)
