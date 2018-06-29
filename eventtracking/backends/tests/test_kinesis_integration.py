"""Test the AWS Kinesis backend"""
from __future__ import absolute_import

from mock import patch
from mock import sentinel

from eventtracking.backends.tests import IntegrationTestCase
from eventtracking.backends.kinesis import KinesisBackend

class TestKinesisIntegrationBackend(IntegrationTestCase):
    """
    # To Test
    # run this in one terminal window - this will monitor the kinesis stream
    # source: https://gist.github.com/LarsFronius/e579051d7f140fd803b0
    # change streamname to be whatever you called your stream (if its not the default one here)
    streamname=eventTrackingTestStream; aws kinesis describe-stream --stream-name $streamname --output text | grep SHARDS | awk '{print $2}' | while read shard; do aws kinesis get-shard-iterator --stream-name $streamname --shard-id $shard --shard-iterator-type TRIM_HORIZON --output text | while read iterator; do while output=`aws kinesis get-records --shard-iterator $iterator --output text`; do iterator=`echo "$output" | head -n1 | awk '{print $2}'`; echo "$output" | gsed 1d | grep RECORDS | while read record; do echo $record | awk '{print $3}' | base64 -D; done; done; done; done

    # run this in another command line window
    nosetests --cover-html --cover-erase --with-coverage  --cover-min-percentage=50 --cover-package=eventtracking --debug=DEFAULT eventtracking/backends/tests/test_kinesis_integration.py
    """
    def setUp(self):
        self.backend = KinesisBackend(streamName='eventTrackingTestStream')

    def test_simple_emit(self):
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
