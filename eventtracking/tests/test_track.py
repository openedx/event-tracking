"""
Test the event tracking module
"""

from __future__ import absolute_import

from datetime import datetime
from unittest import TestCase

from mock import MagicMock
from mock import patch
from mock import sentinel
from mock import call
from pytz import UTC

from eventtracking import tracker


class TestTrack(TestCase):  # pylint: disable=missing-docstring

    def setUp(self):
        self._mock_backend = None
        self._mock_backends = []
        self.tracker = None
        self.configure_mock_backends(1)

        self._expected_timestamp = datetime.now(UTC)
        self._datetime_patcher = patch('eventtracking.tracker.datetime')
        self.addCleanup(self._datetime_patcher.stop)
        mock_datetime = self._datetime_patcher.start()
        mock_datetime.now.return_value = self._expected_timestamp  # pylint: disable=maybe-no-member

    def configure_mock_backends(self, number_of_mocks):
        """Ensure the tracking module has the requisite number of mock backends"""
        backends = {}
        for i in range(number_of_mocks):
            name = 'mock{0}'.format(i)
            backend = MagicMock()
            backends[name] = backend

        self.tracker = tracker.Tracker(backends)
        tracker.register_tracker(self.tracker)
        self._mock_backends = backends.values()
        self._mock_backend = self._mock_backends[0]

    def get_mock_backend(self, index):
        """Get the mock backend created by `configure_mock_backends`"""
        return self.tracker.get_backend('mock{0}'.format(index))

    def test_event_simple_event_without_data(self):
        self.tracker.emit(sentinel.event_type)

        self.assert_backend_called_with(sentinel.event_type)

    def assert_backend_called_with(self, event_type, data=None, context=None, backend=None):
        """Ensures the backend is called exactly once with the expected data."""

        self.assert_exact_backend_calls([(event_type, context, data)], backend=backend)

    def assert_exact_backend_calls(self, parameter_tuple_list, backend=None):
        """
        Ensure the backend was called with the specified parameters in the
        specified order.  Note that it expects a list of tuples to be passed
        in to `parameter_tuple_list`.  Each tuple should be in the form:

        (event_type, context, data)

        These are expanded out into complete events.
        """
        if not backend:
            backend = self._mock_backend

        self.assertEquals(
            backend.send.mock_calls,
            [
                call({
                    'event_type': event_type,
                    'timestamp': self._expected_timestamp,
                    'context': context or {},
                    'data': data or {}
                })
                for event_type, context, data
                in parameter_tuple_list
            ]
        )

    def test_event_simple_event_without_type(self):
        self.tracker.emit(data={sentinel.key: sentinel.value})

        self.assert_backend_called_with(
            'unknown',
            {
                sentinel.key: sentinel.value
            }
        )

    def test_event_simple_event_without_type_or_data(self):
        self.tracker.emit()
        self.assert_backend_called_with(
            'unknown',
            {}
        )

    def test_event_simple_event_with_data(self):
        self.tracker.emit(
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
        self.tracker.emit(sentinel.event_type)

        for backend in self._mock_backends:
            self.assert_backend_called_with(
                sentinel.event_type, backend=backend)

    def test_single_backend_failure(self):
        self.configure_mock_backends(2)
        self.get_mock_backend(0).send.side_effect = Exception

        self.tracker.emit(sentinel.event_type)

        self.assert_backend_called_with(
            sentinel.event_type, backend=self.get_mock_backend(1))

    def test_global_tracker(self):
        tracker.emit(sentinel.event_type)

        self.assert_backend_called_with(
            sentinel.event_type)

    def test_missing_tracker(self):
        self.assertRaises(KeyError, tracker.get_tracker, 'foobar')

    def test_single_context(self):
        context = {sentinel.context_key: sentinel.context_value}
        data = {sentinel.key: sentinel.value}

        self.tracker.enter_context('single', context)
        self.tracker.emit(sentinel.event_type, data)
        self.tracker.exit_context('single')

        self.assert_backend_called_with(
            sentinel.event_type,
            data=data,
            context=context
        )

    def test_context_override(self):
        context = {
            sentinel.context_key: sentinel.context_value,
            sentinel.another_key: sentinel.another_value
        }
        override_context = {
            sentinel.context_key: sentinel.override_context_value
        }
        with self.tracker.context('outer', context):
            with self.tracker.context('inner', override_context):
                self.tracker.emit(sentinel.event_type)

        self.assert_backend_called_with(
            sentinel.event_type,
            context={
                sentinel.context_key: sentinel.override_context_value,
                sentinel.another_key: sentinel.another_value
            }
        )

    def test_exception_in_context(self):
        with self.assertRaises(ValueError):
            with self.tracker.context('foo', {sentinel.context_key: sentinel.context_value}):
                raise ValueError

        self.tracker.emit(sentinel.event_type)

        self.assert_backend_called_with(sentinel.event_type)
