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
                'ip': "your IP address",
                'agent': "your user-agent string",
                'path': "your path",
                'page': "your page",
                'referer': "your referrer",
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
        ip_address = context.get('ip')
        if ip_address is not None:
            segment_context['ip'] = ip_address
        user_agent = context.get('agent')
        if user_agent is not None:
            segment_context['userAgent'] = user_agent
        path = context.get('path')
        referer = context.get('referer')
        page = context.get('page')
        if path is not None or referer is not None or page is not None:
            segment_context['page'] = {}
            if path is not None:
                segment_context['page']['path'] = path
            if referer is not None:
                segment_context['page']['referrer'] = referer
            if page is not None:
                segment_context['page']['url'] = page

        analytics.track(
            user_id,
            name,
            event,
            context=segment_context
        )
