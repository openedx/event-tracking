"""
Test the async routing backend.
"""

import json
from datetime import datetime
from unittest import TestCase
from unittest.mock import patch

from django.test import override_settings
from openedx_events.analytics.data import TrackingLogData

from eventtracking.backends.event_bus import EventBusRoutingBackend


class TestAsyncRoutingBackend(TestCase):
    """
    Test the async routing backend.
    """

    def setUp(self):
        super().setUp()
        self.sample_event = {
            "name": "sample_event",
            "data": {"foo": "bar"},
            "timestamp": "2020-01-01T12:12:12.000000+00:00",
            "context": {"baz": "qux"},
        }

    @patch("eventtracking.backends.event_bus.EventBusRoutingBackend.send")
    def test_successful_send(self, mocked_send_event):
        backend = EventBusRoutingBackend()
        backend.send(self.sample_event)
        mocked_send_event.assert_called_once_with(self.sample_event)

    @override_settings(
        SEND_TRACKING_EVENT_EMITTED_SIGNAL=True,
        EVENT_BUS_TRACKING_LOGS=["sample_event"],
    )
    @patch("eventtracking.backends.event_bus.TRACKING_EVENT_EMITTED.send_event")
    def test_successful_send_event(self, mock_send_event):
        backend = EventBusRoutingBackend()
        backend.send(self.sample_event)

        mock_send_event.assert_called()
        self.assertDictContainsSubset(
            {
                "tracking_log": TrackingLogData(
                    name=self.sample_event["name"],
                    timestamp=datetime.strptime(
                        self.sample_event["timestamp"], "%Y-%m-%dT%H:%M:%S.%f%z"
                    ),
                    data=json.dumps(self.sample_event["data"]),
                    context=json.dumps(self.sample_event["context"]),
                )
            },
            mock_send_event.call_args.kwargs,
        )

    @patch(
        "eventtracking.backends.event_bus.SEND_TRACKING_EVENT_EMITTED_SIGNAL.is_enabled"
    )
    @patch("eventtracking.backends.event_bus.TRACKING_EVENT_EMITTED.send_event")
    def test_event_is_disabled(self, mock_send_event, mock_is_enabled):
        mock_is_enabled.return_value = False
        backend = EventBusRoutingBackend()
        backend.send(self.sample_event)
        mock_is_enabled.assert_called_once()
        mock_send_event.assert_not_called()
