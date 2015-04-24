"""Test the segment.com backend"""

from __future__ import absolute_import

from unittest import TestCase
from mock import patch
from mock import sentinel

from eventtracking.backends.segment import SegmentBackend


class TestSegmentBackend(TestCase):
    """Test the segment.com backend"""

    def setUp(self):
        patcher = patch('eventtracking.backends.segment.analytics')
        self.addCleanup(patcher.stop)
        self.mock_analytics = patcher.start()
        self.backend = SegmentBackend()

    def test_simple_emit(self):
        event = {
            'name': sentinel.name,
            'context': {
                'user_id': sentinel.user_id
            },
            'data': {
                'foo': sentinel.bar
            }
        }
        self.backend.send(event)
        self.mock_analytics.track.assert_called_once_with(sentinel.user_id, sentinel.name, event, context={})

    def test_missing_name(self):
        event = {}
        self.backend.send(event)
        self.assert_no_event_emitted()

    def assert_no_event_emitted(self):
        """Ensure no event was actually sent to segment.com"""
        self.assertEqual(len(self.mock_analytics.mock_calls), 0)

    def test_missing_context(self):
        event = {
            'name': sentinel.name,
        }
        self.backend.send(event)
        self.assert_no_event_emitted()

    def test_missing_user_id(self):
        event = {
            'name': sentinel.name,
            'context': {}
        }
        self.backend.send(event)
        self.assert_no_event_emitted()

    def test_google_analytics_client_id(self):
        event = {
            'name': sentinel.name,
            'context': {
                'user_id': sentinel.user_id,
                'client_id': sentinel.client_id
            }
        }
        expected_segment_context = {
            'Google Analytics': {
                'clientId': sentinel.client_id
            }
        }
        self.backend.send(event)
        self.mock_analytics.track.assert_called_once_with(
            sentinel.user_id, sentinel.name, event, context=expected_segment_context)


class TestSegmentBackendMissingDependency(TestCase):
    """Test the segment.com backend without the package installed"""

    def test_no_analytics_api(self):
        event = {
            'name': sentinel.name,
            'context': {
                'user_id': sentinel.user_id
            },
            'data': {
                'foo': sentinel.bar
            }
        }
        backend = SegmentBackend()
        backend.send(event)
