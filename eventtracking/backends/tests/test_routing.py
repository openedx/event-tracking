"""Test the routing backend"""


from unittest import TestCase

from unittest.mock import MagicMock, sentinel

from eventtracking.backends.routing import RoutingBackend
from eventtracking.processors.exceptions import EventEmissionExit


class TestRoutingBackend(TestCase):
    """Test the routing backend"""

    def setUp(self):
        super().setUp()
        self.sample_event = {'name': sentinel.name}

        self.mock_backend = MagicMock()
        self.router = RoutingBackend(backends={'0': self.mock_backend})

    def test_non_callable_backend(self):
        with self.assertRaisesRegexp(  # pylint: disable=deprecated-method,useless-suppression
                ValueError, r'Backend \w+ does not have a callable "send" method.'):
            RoutingBackend(backends={
                'a': 'b'
            })

    def test_backend_without_send(self):
        with self.assertRaisesRegexp(  # pylint: disable=deprecated-method,useless-suppression
                ValueError, r'Backend \w+ does not have a callable "send" method.'):
            RoutingBackend(backends={
                'a': object()
            })

    def test_non_callable_processor(self):
        with self.assertRaisesRegexp(  # pylint: disable=deprecated-method,useless-suppression
                ValueError, r'Processor \w+ is not callable.'):
            RoutingBackend(processors=[
                object()
            ])

    def test_non_callable_processor_simple_type(self):
        with self.assertRaisesRegexp(  # pylint: disable=deprecated-method,useless-suppression
                ValueError, r'Processor \w+ is not callable.'):
            RoutingBackend(processors=[
                'b'
            ])

    def test_single_processor(self):
        mock_processor = MagicMock()
        router = RoutingBackend(processors=[
            mock_processor
        ])
        router.send(self.sample_event)
        mock_processor.assert_called_once_with(self.sample_event)

    def test_single_backend(self):
        mock_backend = MagicMock()
        router = RoutingBackend(backends={
            'mock0': mock_backend
        })
        router.send(self.sample_event)
        mock_backend.send.assert_called_once_with(self.sample_event)

    def test_multiple_backends(self):
        backends = {
            str(i): MagicMock()
            for i in range(5)
        }
        router = RoutingBackend(backends=backends)
        router.send(self.sample_event)
        for backend in backends.values():
            backend.send.assert_called_once_with(self.sample_event)

    def test_backend_failure(self):
        backends = {
            str(i): MagicMock()
            for i in range(5)
        }
        backends['1'].send.side_effect = RuntimeError
        router = RoutingBackend(backends=backends)
        router.send(self.sample_event)
        for backend in backends.values():
            backend.send.assert_called_once_with(self.sample_event)

    def test_multiple_processors(self):
        processors = [
            MagicMock()
            for __ in range(5)
        ]
        for processor in processors:
            processor.return_value = self.sample_event
        router = RoutingBackend(processors=processors)
        router.send(self.sample_event)
        for processor in processors:
            processor.assert_called_once_with(self.sample_event)

    def test_multiple_backends_and_processors(self):
        backends = {
            str(i): MagicMock()
            for i in range(5)
        }
        processors = [
            MagicMock()
            for __ in range(5)
        ]
        for processor in processors:
            processor.return_value = self.sample_event

        router = RoutingBackend(backends=backends, processors=processors)
        router.send(self.sample_event)
        for processor in processors:
            processor.assert_called_once_with(self.sample_event)
        for backend in backends.values():
            backend.send.assert_called_once_with(self.sample_event)

    def test_callable_class_processor(self):
        class SampleProcessor:
            """An event processing class"""

            def __call__(self, event):
                """Modify the event type"""
                event['name'] = sentinel.changed_name

        self.router.register_processor(SampleProcessor())
        self.router.send(self.sample_event)
        self.assert_single_event_emitted({'name': sentinel.changed_name})

    def assert_single_event_emitted(self, event):
        """Assert that the mock backend is called exactly once with the provided event"""
        self.mock_backend.send.assert_called_once_with(event)

    def test_function_processor(self):
        def change_name(event):
            """Modify the event type of the event"""
            event['name'] = sentinel.changed_name
            return event

        self.router.register_processor(change_name)
        self.router.send(self.sample_event)
        self.assert_single_event_emitted({'name': sentinel.changed_name})

    def test_processor_chain(self):

        def change_name(event):
            """Modify the event type of the event"""
            event['name'] = sentinel.changed_name
            return event

        def inject_fields(event):
            """Add a couple fields to the event"""
            event['other'] = sentinel.other
            event['to_remove'] = sentinel.to_remove
            return event

        def remove_field(event):
            """Remove a field to the event"""
            self.assertEqual(event['to_remove'], sentinel.to_remove)
            del event['to_remove']
            return event

        def ensure_modified_event(event):
            """Assert the first processor added a field to the event"""
            self.assertEqual(event['name'], sentinel.changed_name)
            self.assertEqual(event['other'], sentinel.other)
            return event

        self.router.register_processor(change_name)
        self.router.register_processor(inject_fields)
        self.router.register_processor(remove_field)
        self.router.register_processor(ensure_modified_event)
        self.router.send(self.sample_event)

        self.assert_single_event_emitted(
            {
                'name': sentinel.changed_name,
                'other': sentinel.other
            }
        )

    def test_processor_failure(self):

        def always_fail(event):  # pylint: disable=unused-argument, useless-suppression
            """Always raises an error"""
            raise ValueError

        def change_name(event):
            """Modify the event type of the event"""
            event['name'] = sentinel.changed_name
            return event

        self.router.register_processor(always_fail)
        self.router.register_processor(change_name)
        self.router.send(self.sample_event)
        self.assert_single_event_emitted({'name': sentinel.changed_name})

    def test_processor_returns_none(self):

        def return_none(event):  # pylint: disable=unused-argument
            """Don't return the event"""

        self.router.register_processor(return_none)
        self.router.send(self.sample_event)
        self.assert_single_event_emitted(self.sample_event)

    def test_processor_modifies_the_same_event_object(self):

        def forget_return(event):
            """Modify the event without returning it"""
            event['name'] = sentinel.forgotten_return

        def ensure_name_changed(event):
            """Assert the event type has been modified even though the event wasn't returned"""
            self.assertEqual(event['name'], sentinel.forgotten_return)

        self.router.register_processor(forget_return)
        self.router.register_processor(ensure_name_changed)
        self.router.send(self.sample_event)
        self.assert_single_event_emitted({'name': sentinel.forgotten_return})

    def test_processor_abort(self):

        def abort_processing(event):  # pylint: disable=unused-argument, useless-suppression
            """Always abort processing"""
            raise EventEmissionExit

        def fail_if_called(event):  # pylint: disable=unused-argument
            """Fail the test immediately if this is called"""
            self.fail('This processor should never be called')

        self.router.register_processor(abort_processing)
        self.router.register_processor(fail_if_called)
        self.router.send(self.sample_event)
        self.assertEqual(len(self.mock_backend.mock_calls), 0)

    def test_nested_routing_with_abort(self):
        mock_abort_processing = MagicMock()
        mock_abort_processing.side_effect = EventEmissionExit

        left_backend = MagicMock()
        left_router = RoutingBackend(backends={'0': left_backend}, processors=[mock_abort_processing])

        right_backend = MagicMock()
        right_router = RoutingBackend(backends={'0': right_backend})

        root_router = RoutingBackend(backends={
            'left': left_router,
            'right': right_router,
        })

        root_router.send(self.sample_event)

        right_backend.send.assert_called_once_with(self.sample_event)
        self.assertEqual(len(left_backend.mock_calls), 0)
        mock_abort_processing.assert_called_once_with(self.sample_event)

    def test_backend_call_order(self):

        class OrderRecordingBackend:
            """Keep track of the order that the backends are called in"""

            def __init__(self, name, call_order):
                self._name = name
                self._order = call_order

            def send(self, event):  # pylint: disable=unused-argument
                """Do nothing except record that this was called"""
                self._order.append(self._name)

        call_order = []
        backends = {
            str(i): OrderRecordingBackend(str(i), call_order)
            for i in range(5)
        }

        router = RoutingBackend(backends=backends)

        router.send(self.sample_event)
        self.assertEqual(call_order, ['0', '1', '2', '3', '4'])
