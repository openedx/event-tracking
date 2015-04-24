"""Event tracking backend that sends events to segment.com"""

from __future__ import absolute_import

try:
    import analytics
except ImportError:
    analytics = None


class SegmentBackend(object):
    """

    Send events to segment.com

    It is assumed that other code elsewhere initializes the segment.com API and makes calls to analytics.identify.

    Requires all emitted events to have the following structure (at a minimum)::

        {
            'name': 'something',
            'context': {
                'user_id': 10,
            }
        }

    Additionally, the following fields can optionally be defined::

        {
            'context': {
                'client_id': "your google analytics client id",
            }
        }

    Note that although some parts of the event are lifted out to pass explicitly into the Segment.com API, the entire
    event is sent as the payload to segment.com, which includes all context, data and other fields in the event.

    """

    def send(self, event):
        """Use the segment.com python API to send the event to segment.com"""
        if analytics is None:
            return

        context = event.get('context', {})
        user_id = context.get('user_id')
        name = event.get('name')
        if name is None or user_id is None:
            return

        segment_context = {}

        ga_client_id = context.get('client_id')
        if ga_client_id is not None:
            segment_context['Google Analytics'] = {
                'clientId': ga_client_id
            }

        analytics.track(
            user_id,
            name,
            event,
            context=segment_context
        )
