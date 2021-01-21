"""
Runs invasive tests to ensure that the tracking system can communicate with
the actual python logging system.
"""


import json
import logging
import os
import tempfile
from datetime import datetime

from pytz import UTC

from eventtracking.backends.logger import LoggerBackend
from eventtracking.backends.tests import InMemoryBackend, IntegrationTestCase
from eventtracking.tracker import Tracker


class TestLoggerIntegration(IntegrationTestCase):
    """
    Writes a real log file and ensures the messages are written properly.
    """

    def setUp(self):

        super().setUp()
        logger_name = 'integration.test'
        test_logger = logging.getLogger(logger_name)
        test_logger.setLevel(logging.INFO)

        self.temporary_fd, self.temporary_file_name = tempfile.mkstemp()
        self.addCleanup(os.remove, self.temporary_file_name)

        self.temporary_file_handler = logging.FileHandler(self.temporary_file_name, mode='w', encoding='utf_8')
        self.temporary_file_handler.setFormatter(logging.Formatter(fmt='%(message)s'))
        test_logger.addHandler(self.temporary_file_handler)
        self.addCleanup(test_logger.removeHandler, self.temporary_file_handler)

        self.logger_backend = LoggerBackend(name=logger_name)
        self.memory_backend = InMemoryBackend()
        self.tracker = Tracker({
            'logger': self.logger_backend,
            'mem': self.memory_backend
        })

    def test_sequential_events(self):
        now = datetime.now(UTC)
        for i in range(10):
            self.tracker.emit('org.test.logger.integration', {
                'email': 'tester@eventtracking.org',
                'sequence': i,
                'current_time': now
            })

        # The custom JSON encoder will string encode these fields, however
        # it is not used to decode the events, so we need to compare these
        # fields as strings.
        for event in self.memory_backend.events:
            event['timestamp'] = event['timestamp'].isoformat()
            event['data']['current_time'] = event['data']['current_time'].isoformat()
        self.assertEqual(len(self.memory_backend.events), 10)

        written_events = []
        with os.fdopen(self.temporary_fd, 'r') as temporary_file:
            for line in temporary_file:
                loaded_event = json.loads(line.strip())
                written_events.append(loaded_event)

        self.assertEqual(written_events, self.memory_backend.events)
