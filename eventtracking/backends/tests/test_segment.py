"""Test the segment.com backend"""


from unittest import TestCase
from unittest.mock import patch
from unittest.mock import sentinel

from eventtracking.backends.segment import SegmentBackend


class TestSegmentBackend(TestCase):
    """Test the segment.com backend"""

    def setUp(self):
        super().setUp()
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

    def test_ip_address(self):
        event = {
            'name': sentinel.name,
            'context': {
                'user_id': sentinel.user_id,
                'ip': sentinel.ip
            }
        }
        expected_segment_context = {
            'ip': sentinel.ip
        }
        self.backend.send(event)
        self.mock_analytics.track.assert_called_once_with(
            sentinel.user_id, sentinel.name, event, context=expected_segment_context)

    def test_user_agent(self):
        event = {
            'name': sentinel.name,
            'context': {
                'user_id': sentinel.user_id,
                'agent': sentinel.user_agent
            }
        }
        expected_segment_context = {
            'userAgent': sentinel.user_agent
        }
        self.backend.send(event)
        self.mock_analytics.track.assert_called_once_with(
            sentinel.user_id, sentinel.name, event, context=expected_segment_context)

    def test_path(self):
        event = {
            'name': sentinel.name,
            'context': {
                'user_id': sentinel.user_id,
                'path': sentinel.path
            }
        }
        expected_segment_context = {
            'page': {
                'path': sentinel.path
            }
        }
        self.backend.send(event)
        self.mock_analytics.track.assert_called_once_with(
            sentinel.user_id, sentinel.name, event, context=expected_segment_context)

    def test_referer(self):
        event = {
            'name': sentinel.name,
            'context': {
                'user_id': sentinel.user_id,
                'referer': sentinel.referer
            }
        }
        expected_segment_context = {
            'page': {
                'referrer': sentinel.referer
            }
        }
        self.backend.send(event)
        self.mock_analytics.track.assert_called_once_with(
            sentinel.user_id, sentinel.name, event, context=expected_segment_context)

    def test_page(self):
        event = {
            'name': sentinel.name,
            'context': {
                'user_id': sentinel.user_id,
                'page': sentinel.page
            }
        }
        expected_segment_context = {
            'page': {
                'url': sentinel.page
            }
        }
        self.backend.send(event)
        self.mock_analytics.track.assert_called_once_with(
            sentinel.user_id, sentinel.name, event, context=expected_segment_context)

    def test_host_and_path_with_missing_page(self):
        event = {
            'name': sentinel.name,
            'context': {
                'user_id': sentinel.user_id,
                # Note that 'host' and 'path' will be urlparsed, so must be strings.
                'path': '/this/is/a/path',
                'host': 'hostname',
            }
        }
        expected_segment_context = {
            'page': {
                'path': '/this/is/a/path',
                'url': 'https://hostname/this/is/a/path'  # Synthesized URL value.
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
