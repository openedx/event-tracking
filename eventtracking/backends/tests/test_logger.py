"""Test the logging backend"""


import json
import datetime
from unittest import TestCase

from unittest.mock import patch
from unittest.mock import sentinel
import pytz

from eventtracking.backends.logger import LoggerBackend


class TestLoggerBackend(TestCase):
    """Test the logging backend"""

    def setUp(self):
        super().setUp()
        patcher = patch('eventtracking.backends.logger.logging')
        self.mock_logging = patcher.start()
        self.addCleanup(patcher.stop)
        self.mock_logger = self.mock_logging.getLogger.return_value

        # This will call the mocks
        self.backend = LoggerBackend()

        # Reset them so that we get "clean" mocks in our tests
        self.mock_logging.reset_mock()
        self.mock_logger.reset_mock()

    def test_logs_to_correct_named_logger(self):
        backend = LoggerBackend(name=sentinel.logger_name)
        self.mock_logging.getLogger.assert_called_once_with(sentinel.logger_name)
        backend.send({})
        self.assert_event_emitted({})

    def assert_event_emitted(self, event):
        """Asserts exactly one event was emitted"""
        self.mock_logger.info.assert_called_once_with(
            json.dumps(event)
        )

    def test_unserializable_event(self):
        with self.assertRaises(TypeError):
            self.backend.send({'foo': object()})
        self.assert_no_events_emitted()

    def assert_no_events_emitted(self):
        """Asserts no events have been emitted"""
        self.assertFalse(self.mock_logger.info.called)

    def test_big_event(self):
        backend = LoggerBackend(max_event_size=10)
        backend.send({'foo': 'a'*(backend.max_event_size + 1)})
        self.assert_no_events_emitted()

    def test_unlimited_event_size(self):
        default_max_event_size = self.backend.max_event_size
        backend = LoggerBackend(max_event_size=None)
        event = {'foo': 'a'*(default_max_event_size + 1)}
        backend.send(event)
        self.assert_event_emitted(event)

    def test_event_with_datetime_fields(self):
        eastern_tz = pytz.timezone('US/Eastern')
        test_time = datetime.datetime(2012, 5, 1, 7, 27, 1, 200)
        event = {
            'test': True,
            'time': test_time,
            'converted_time': eastern_tz.localize(test_time),
            'date': datetime.date(2012, 5, 7)
        }

        self.backend.send(event)
        self.assert_event_emitted({
            'test': True,
            'time': '2012-05-01T07:27:01.000200+00:00',
            'converted_time': '2012-05-01T11:27:01.000200+00:00',
            'date': '2012-05-07'
        })

    def test_multiple_events(self):
        for event in [{'a': 'a'}, {'b': 'b'}]:
            self.backend.send(event)
            self.assert_event_emitted(event)
            self.mock_logger.info.reset_mock()

    def test_dynamic_level(self):
        backend = LoggerBackend(level='warning')
        backend.send({})
        self.assertFalse(self.mock_logger.info.called)
        self.mock_logger.warning.assert_called_once_with('{}')
