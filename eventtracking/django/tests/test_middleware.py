"""Tests for the middleware"""

from __future__ import absolute_import

from mock import patch
from mock import sentinel

from django.test import TestCase
from django.test.client import RequestFactory
from django.test.utils import override_settings

from eventtracking.django.middleware import TrackRequestContextMiddleware
from eventtracking.django.middleware import TrackRequestMiddleware


class TestTrackRequestContextMiddleware(TestCase):
    """Test middleware that adds context to every request"""

    def setUp(self):
        get_tracker_patcher = patch('eventtracking.django.middleware.track.get_tracker')
        mock_get_tracker = get_tracker_patcher.start()
        self.addCleanup(get_tracker_patcher.stop)

        self.mock_tracker = mock_get_tracker.return_value

        self.middleware = TrackRequestContextMiddleware()
        self.request_factory = RequestFactory()

    def test_simple_request(self):
        request = self.request_factory.get('/somewhere')
        self.middleware.process_request(request)

        self.mock_tracker.enter_context.assert_called_once_with(
            'django.context',
            {
                'username': '',
                'user_primary_key': '',
                'ip': '127.0.0.1',
                'agent': '',
                'host': 'testserver',
                'session': '',
                'path': '/somewhere'
            }
        )

        resp = self.middleware.process_response(request, sentinel.response)
        self.mock_tracker.exit_context.assert_called_once_with('django.context')
        self.assertEquals(resp, sentinel.response)


class TestTrackRequestMiddleware(TestCase):
    """Test the middleware that tracks every request"""

    def setUp(self):
        self.track_middleware = TrackRequestMiddleware()
        self.request_factory = RequestFactory()

        track_patcher = patch('eventtracking.django.middleware.track.event')
        self.mock_track = track_patcher.start()
        self.addCleanup(track_patcher.stop)

    def test_normal_request(self):
        request = self.request_factory.get('/somewhere')
        self.track_middleware.process_response(request, None)
        self.assert_event_was_emitted()

    def assert_event_was_emitted(self):
        """Fail if no event was emitted"""
        self.assertTrue(self.mock_track.called)

    @override_settings(TRACKING_IGNORE_URL_PATTERNS=[])
    def test_reading_filtered_urls_from_settings(self):
        request = self.request_factory.get('/event')
        self.track_middleware.process_response(request, None)
        self.assert_event_was_emitted()

    @override_settings(TRACKING_IGNORE_URL_PATTERNS=[r'^/some/excluded.*'])
    def test_anchoring_of_patterns_at_beginning(self):
        request = self.request_factory.get('/excluded')
        self.track_middleware.process_response(request, None)
        self.assert_event_was_emitted()
        self.mock_track.reset_mock()

        request = self.request_factory.get('/some/excluded/url')
        self.track_middleware.process_response(request, None)
        self.assert_event_was_not_emitted()

    def assert_event_was_not_emitted(self):
        """Fail if an event was emitted"""
        self.assertFalse(self.mock_track.called)

    @override_settings(DEBUG=False)
    def test_does_not_fail(self):
        self.mock_track.side_effect = Exception
        request = self.request_factory.get('/anywhere')

        self.track_middleware.process_response(request, None)
        # Ensure the exception isn't propogated out to the caller

    @override_settings(DEBUG=True)
    def test_fails_in_debug_mode(self):
        self.mock_track.side_effect = Exception
        request = self.request_factory.get('/anywhere')

        with self.assertRaises(Exception):
            self.track_middleware.process_response(request, None)

    def test_get_request_parameters_are_included(self):
        test_request_params = dict()
        for param in ['foo', 'bar', 'baz']:
            test_request_params[param] = param

        request = self.request_factory.get('/anywhere', test_request_params)
        self.track_middleware.process_response(request, None)

        self.assert_exactly_one_event_emitted_with({'method': 'GET', 'body': {}, 'query': test_request_params})

    def assert_exactly_one_event_emitted_with(self, data):
        """Ensure exactly one event was emitted with the given data"""
        self.mock_track.assert_called_once_with('http.request', data)

    def test_passwords_stripped_from_request(self):
        test_request_params = dict()
        expected_event_data = dict()
        for param in ['password', 'newpassword', 'new_password', 'oldpassword', 'old_password']:
            test_request_params[param] = sentinel.password
            expected_event_data[param] = ''

        test_request_params['other_field'] = 'other value'
        expected_event_data['other_field'] = test_request_params['other_field']

        request = self.request_factory.get('/anywhere', test_request_params)
        self.track_middleware.process_response(request, None)

        self.assert_exactly_one_event_emitted_with({'method': 'GET', 'body': {}, 'query': expected_event_data})

    @override_settings(TRACKING_HTTP_REQUEST_EVENT_TYPE='custom.event')
    def test_setting_override_event_type(self):
        request = self.request_factory.get('/anywhere')
        self.track_middleware.process_response(request, None)

        self.mock_track.assert_called_once_with('custom.event', {'method': 'GET', 'body': {}, 'query': {}})
