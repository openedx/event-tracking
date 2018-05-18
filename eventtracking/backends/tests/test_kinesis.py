"""Test the AWS Kinesis backend"""

from __future__ import absolute_import

from unittest import TestCase
from mock import patch
from mock import sentinel

from eventtracking.backends.kinesis import KinesisBackend

class TestKinesisBackend(TestCase):
    """Test the AWS Kinesis backend"""

    def setUp(self):
        #patch('boto.utils', 'get_instance_identity', {'document': {'region': 'us-east-1'}})

        patcher = patch('eventtracking.backends.kinesis.boto')
        self.mock_boto = patcher.start()
        self.addCleanup(patcher.stop)

        self.backend = KinesisBackend()

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
        #self.mock_kinesis.put_records.assert_called_once_with(sentinel.user_id, sentinel.name, event, context={})

    def test_missing_name(self):
        event = {}
        self.backend.send(event)
        self.assert_no_event_emitted()

    def assert_no_event_emitted(self):
        """Ensure no event was actually sent to Kinesis"""
        self.assertEqual(len(self.mock_boto.mock_calls), 0)

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


class TestSegmentBackendMissingDependency(TestCase):
    """Test the Kinesis backend without the package installed"""

    def test_no_boto(self):
        event = {
            'name': sentinel.name,
            'context': {
                'user_id': sentinel.user_id
            },
            'data': {
                'foo': sentinel.bar
            }
        }
        backend = KinesisBackend()
        backend.send(event)
