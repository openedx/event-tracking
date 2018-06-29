"""Event tracking backend that sends events to an AWS Kinesis Stream"""

from __future__ import absolute_import
from boto import kinesis

from datetime import datetime, date
from pytz import UTC
import json
import logging

log = logging.getLogger(__name__)

class KinesisBackend(object):

    def __init__(self, **kwargs):

        """
        Event tracker backend that uses a Kinesis Stream

        `streamName` is the stream to send the events to
        """

        self.streamName = kwargs.get('streamName', None)
        self.regionName = kwarge.get('regionName', None)
        self.kinesis = kinesis.connect_to_region(self.regionName)

    """
    Send events to an AWS Kinesis Stream

    It is assumed that other code elsewhere establishes the permissions to write to the Kinesis Stream

    Requires all emitted events to have the following structure (at a minimum)::

        {
            'name': 'something',
            'context': {
                'user_id': 10,
            }
        }
    """

    def send(self, event):
        # validate
        context = event.get('context', {})
        user_id = context.get('user_id')
        name = event.get('name')
        if name is None or user_id is None:
            log.info('Ignoring Event:')
            return

        log.info(event)
        kinesisData = {
            'Data': json.dumps(event, cls=DateTimeJSONEncoder),
            'PartitionKey': 'shardId-000000000000'
        }

        log.info(kinesisData)
        log.info(self.streamName)

        self.kinesis.put_record([ kinesisData ], self.streamName)


class DateTimeJSONEncoder(json.JSONEncoder):
    """JSON encoder aware of datetime.datetime and datetime.date objects"""

    def default(self, obj):  # lint-amnesty, pylint: disable=arguments-differ, method-hidden
        """
        Serialize datetime and date objects of iso format.

        datatime objects are converted to UTC.
        """

        if isinstance(obj, datetime):
            if obj.tzinfo is None:
                # Localize to UTC naive datetime objects
                obj = UTC.localize(obj)  # pylint: disable=no-value-for-parameter
            else:
                # Convert to UTC datetime objects from other timezones
                obj = obj.astimezone(UTC)
            return obj.isoformat()
        elif isinstance(obj, date):
            return obj.isoformat()

        return super(DateTimeJSONEncoder, self).default(obj)
