"""Event tracking backend that sends events to segment.com"""

from six.moves.urllib.parse import urlunsplit

try:
    import analytics
except ImportError:
    analytics = None


class SegmentBackend:
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
                'agent': "your user-agent string",
                'client_id': "your google analytics client id",
                'host': "your hostname",
                'ip': "your IP address",
                'page': "your page",
                'path': "your path",
                'referer': "your referrer",
            }
        }

    The 'page', 'path' and 'referer' are sent to Segment as "page" information.  If the 'page' is absent but the 'host'
    and 'path' are present, these are used to create a URL value to substitute for the 'page' value.

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

        if path and not page:
            # Try to put together a url from host and path, hardcoding the schema.
            # (Segment doesn't care about the schema for GA, but will extract the host and path from the url.)
            host = context.get('host')
            if host:
                parts = ("https", host, path, "", "")
                page = urlunsplit(parts)

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
