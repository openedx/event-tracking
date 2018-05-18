"""Event tracking backend that sends events to an AWS Kinesis Stream"""

from __future__ import absolute_import

try:
    import boto
except ImportError:
    boto = None

import logging
log = logging.getLogger(__name__)

class KinesisBackend(object):

    # def __init__(self):
    #     if boto is None:
    #         log.error('boto not loaded')
    #         return

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
        if boto is None:
            log.debug('boto not loaded')
            return

        # validate
        context = event.get('context', {})
        user_id = context.get('user_id')
        name = event.get('name')
        if name is None or user_id is None:
            log.error('Ignoring Event:')
            log.debug(event)
            return

        data = boto.utils.get_instance_identity()
        region_name = data['document']['region']

        self.kinesis = boto.kinesis.connect_to_region(region_name)

        # send!!
        self.kinesis.put_records([ event ], "BotoDemo")
