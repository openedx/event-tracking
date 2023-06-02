"""
Test the async routing backend.
"""
from unittest import TestCase

from unittest.mock import sentinel, patch
from eventtracking.backends.event_bus import EventBusRoutingBackend
from openedx_events.analytics.data import TrackingLogData

class TestAsyncRoutingBackend(TestCase):
    """
    Test the async routing backend.
    """

    def setUp(self):
        super().setUp()
        self.sample_event = {
            'name': str(sentinel.name),
            'data': 'data',
            'timestamp': '2020-01-01T12:12:12.000000+00:00',
            'context': {},
        }

    @patch('eventtracking.backends.event_bus.EventBusRoutingBackend.send')
    def test_successful_send(self, mocked_send_event):
        backend = EventBusRoutingBackend()
        backend.send(self.sample_event)
        mocked_send_event.assert_called_once_with(self.sample_event)

    @patch('eventtracking.backends.event_bus.TRACKING_EVENT_EMITTED.send_event')
    def test_successful_send_event(self, mocked_send_event):
        backend = EventBusRoutingBackend()
        backend.send(self.sample_event)
        mocked_send_event.assert_called_once_with(
            tracking_log=TrackingLogData(
                name=self.sample_event['name'],
                timestamp=self.sample_event['timestamp'],
                data=self.sample_event['data'],
                context=self.sample_event['context']
            )
        )
