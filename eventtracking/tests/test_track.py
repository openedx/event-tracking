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
        self.tracker.emit(sentinel.name)

        self.assert_backend_called_with(sentinel.name)

    def assert_backend_called_with(self, name, data=None, context=None, backend=None):
        """Ensures the backend is called exactly once with the expected data."""

        self.assert_exact_backend_calls([(name, context, data)], backend=backend)

    def assert_exact_backend_calls(self, parameter_tuple_list, backend=None):
        """
        Ensure the backend was called with the specified parameters in the
        specified order.  Note that it expects a list of tuples to be passed
        in to `parameter_tuple_list`.  Each tuple should be in the form:

        (name, context, data)

        These are expanded out into complete events.
        """
        if not backend:
            backend = self._mock_backend

        self.assertEquals(
            backend.send.mock_calls,
            [
                call({
                    'name': name,
                    'timestamp': self._expected_timestamp,
                    'context': context or {},
                    'data': data or {}
                })
                for name, context, data
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
            sentinel.name,
            {
                sentinel.key: sentinel.value
            }
        )

        self.assert_backend_called_with(
            sentinel.name,
            {
                sentinel.key: sentinel.value
            }
        )

    def test_multiple_backends(self):
        self.configure_mock_backends(2)
        self.tracker.emit(sentinel.name)

        for backend in self._mock_backends:
            self.assert_backend_called_with(
                sentinel.name, backend=backend)

    def test_single_backend_failure(self):
        self.configure_mock_backends(2)
        self.get_mock_backend(0).send.side_effect = Exception

        self.tracker.emit(sentinel.name)

        self.assert_backend_called_with(
            sentinel.name, backend=self.get_mock_backend(1))

    def test_global_tracker(self):
        tracker.emit(sentinel.name)

        self.assert_backend_called_with(
            sentinel.name)

    def test_missing_tracker(self):
        self.assertRaises(KeyError, tracker.get_tracker, 'foobar')

    def test_single_context(self):
        context = {sentinel.context_key: sentinel.context_value}
        data = {sentinel.key: sentinel.value}

        self.tracker.enter_context('single', context)
        self.tracker.emit(sentinel.name, data)
        self.tracker.exit_context('single')

        self.assert_backend_called_with(
            sentinel.name,
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
                self.tracker.emit(sentinel.name)

        self.assert_backend_called_with(
            sentinel.name,
            context={
                sentinel.context_key: sentinel.override_context_value,
                sentinel.another_key: sentinel.another_value
            }
        )

    def test_exception_in_context(self):
        with self.assertRaises(ValueError):
            with self.tracker.context('foo', {sentinel.context_key: sentinel.context_value}):
                raise ValueError

        self.tracker.emit(sentinel.name)

        self.assert_backend_called_with(sentinel.name)

    def test_single_processor(self):
        self.tracker.processors.append(self.change_name)
        self.tracker.emit(sentinel.name)
        self.assert_backend_called_with(sentinel.changed_name)

    def change_name(self, event):
        """Modify the event type of the event"""
        event['name'] = sentinel.changed_name
        return event

    def test_non_callable_processor(self):
        self.tracker.processors.append(object())
        self.tracker.emit(sentinel.name)
        self.assert_backend_called_with(sentinel.name)

    def test_callable_class_processor(self):
        class SampleProcessor(object):
            """An event processing class"""
            def __call__(self, event):
                """Modify the event type"""
                event['name'] = sentinel.class_name

        self.tracker.processors.append(SampleProcessor())
        self.tracker.emit(sentinel.name)
        self.assert_backend_called_with(sentinel.class_name)

    def test_processor_chain(self):

        def ensure_modified_event(event):
            """Assert the first processor added a field to the event"""
            self.assertIn(sentinel.key, event)
            self.assertEquals(event[sentinel.key], sentinel.value)
            return event

        self.tracker.processors.extend([self.change_name, ensure_modified_event])
        self.tracker.emit(sentinel.name)
        self.assert_backend_called_with(sentinel.changed_name)

    def test_processor_failure(self):

        def always_fail(event):  # pylint: disable=unused-argument
            """Always raises an error"""
            raise ValueError

        self.tracker.processors.extend([always_fail, self.change_name])
        self.tracker.emit(sentinel.name)
        self.assert_backend_called_with(sentinel.changed_name)

    def test_processor_returns_none(self):

        def return_none(event):  # pylint: disable=unused-argument
            """Don't return the event"""
            pass

        self.tracker.processors.append(return_none)
        self.tracker.emit(sentinel.name)
        self.assert_backend_called_with(sentinel.name)

    def test_processor_modifies_the_same_event_object(self):

        def forget_return(event):
            """Modify the event without returning it"""
            event['name'] = sentinel.forgotten_return

        def ensure_name_changed(event):
            """Assert the event type has been modified even though the event wasn't returned"""
            self.assertEquals(event['name'], sentinel.forgotten_return)

        self.tracker.processors.extend([forget_return, ensure_name_changed])
        self.tracker.emit(sentinel.name)
        self.assert_backend_called_with(sentinel.forgotten_return)
