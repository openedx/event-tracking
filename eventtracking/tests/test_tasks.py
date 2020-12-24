"""
Tests for celery tasks.
"""
import json

from unittest.mock import sentinel

from django.test import TestCase
from django.test.utils import override_settings

from eventtracking.tasks import send_event
from eventtracking.tracker import get_tracker
from eventtracking.django.django_tracker import override_default_tracker
from eventtracking.processors.exceptions import EventEmissionExit


MOCK_EVENT_TRACKING_BACKENDS = {
    'backend_1': {
        'ENGINE': 'eventtracking.backends.routing.RoutingBackend',
        'OPTIONS': {
            'backends': {
                'nested_backend_1': {
                    'ENGINE': 'mock.MagicMock',
                    'OPTIONS': {}
                }
            },
            'processors': [{
                'ENGINE': 'mock.MagicMock',
                'OPTIONS': {}
            }]
        }
    }
}


class TestAsyncSend(TestCase):
    """
    Test `send_event` task.
    """

    def setUp(self):
        super().setUp()

        self.event = {
            'name': str(sentinel.name),
            'event_type': 'edx.test.event',
            'time': '2020-01-01T12:12:12.000000+00:00',
            'event': {
                'key': 'value'
            },
            'session': '0000'
        }

    @override_settings(EVENT_TRACKING_BACKENDS=MOCK_EVENT_TRACKING_BACKENDS)
    def test_event_emission_exit_exception(self):
        override_default_tracker()
        tracker = get_tracker()
        tracker.backends['backend_1'].processors[0].side_effect = EventEmissionExit

        send_event('backend_1', json.dumps(self.event))

        tracker.backends['backend_1'].backends['nested_backend_1'].send.assert_not_called()

    @override_settings(EVENT_TRACKING_BACKENDS=MOCK_EVENT_TRACKING_BACKENDS)
    def test_successful_processing_and_sending_event(self):
        override_default_tracker()
        tracker = get_tracker()
        tracker.backends['backend_1'].processors[0].return_value = self.event

        send_event('backend_1', json.dumps(self.event))

        tracker.backends['backend_1'].backends['nested_backend_1'].send.assert_called_once_with(self.event)
