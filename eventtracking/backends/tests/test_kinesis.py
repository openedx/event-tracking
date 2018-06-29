"""Test the AWS Kinesis backend"""

from __future__ import absolute_import

import boto3

from unittest import TestCase
from mock import patch
from mock import sentinel
from moto import mock_kinesis

from eventtracking.backends.kinesis import KinesisBackend

class TestKinesisBackend(TestCase):
    """Test the AWS Kinesis backend"""

    @mock_kinesis
    def test_simple_emit(self):
        # need to create a stream to test against
        conn = boto3.client('kinesis', region_name="us-east-1")
        conn.create_stream(StreamName='my_stream', ShardCount=1)

        self.backend = KinesisBackend(streamName='my_stream')
        event = {
            'name': 'bob uncle',
            'context': {
                'user_id': 'bob'
            },
            'data': {
                'foo': 'test'
            }
        }
        self.backend.send(event)

    @mock_kinesis
    def test_missing_name(self):
        self.backend = KinesisBackend(streamName='my_stream')
        event = {}
        self.backend.send(event)

    @mock_kinesis
    def test_missing_context(self):
        self.backend = KinesisBackend(streamName='my_stream')
        event = {
            'name': 'bob uncle',
        }
        self.backend.send(event)

    @mock_kinesis
    def test_missing_user_id(self):
        self.backend = KinesisBackend(streamName='my_stream')
        event = {
            'name': 'bob uncle',
            'context': {}
        }
        self.backend.send(event)

# class TestKinesisBackendMissingDependency(TestCase):
#     """Test the Kinesis backend without the package installed"""
#
#     @mock_kinesis
#     def test_no_boto(self):
#         event = {
#             'name': 'bob uncle',
#             'context': {
#                 'user_id': 'bob'
#             },
#             'data': {
#                 'foo': 'test'
#             }
#         }
#         backend = KinesisBackend(streamName='my_stream')
#         backend.send(event)
