"""
Test the async routing backend.
"""
from unittest import TestCase

from unittest.mock import sentinel, patch
from eventtracking.backends.async_routing import AsyncRoutingBackend


class TestAsyncRoutingBackend(TestCase):
    """
    Test the async routing backend.
    """

    def setUp(self):
        super().setUp()
        self.sample_event = {
            'name': str(sentinel.name),
            'event_type': 'edx.test.event',
            'time': '2020-01-01T12:12:12.000000+00:00',
            'event': {
                'key': 'value'
            },
            'session': '0000'
        }

    @patch('eventtracking.backends.async_routing.send_event')
    def test_successful_event_send(self, mocked_send_event):
        backend = AsyncRoutingBackend(backend_name='test')
        processed_event = backend.process_event(self.sample_event)
        backend.send(self.sample_event)
        mocked_send_event.delay.assert_called_once_with('test', processed_event)
