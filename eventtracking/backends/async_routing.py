"""
Route events to processors and backends.
"""
import json
import logging

from eventtracking.backends.routing import RoutingBackend
from eventtracking.backends.logger import DateTimeJSONEncoder
from eventtracking.tasks import send_event


logger = logging.getLogger(__name__)


class AsyncRoutingBackend(RoutingBackend):
    """
    Route events to configured backends asynchronously.

    NB: This can only be safely configured as a top-level backend,
    since the Celery task has to look up the backend again by name.
    This backend can also only be used from the default tracker, since
    again the Celery task does not know which other tracker to use.
    """
    def __init__(self, processors=None, backends=None, backend_name=''):
        self.backend_name = backend_name
        super().__init__(processors=processors, backends=backends)

    def send(self, event):
        """
        Send event to registered backends asynchronously.

        Arguments:
            event (dict) :  Open edX generated analytics event
        """
        try:
            json_event = json.dumps(event, cls=DateTimeJSONEncoder)
            send_event.delay(self.backend_name, json_event)
            logger.info('Scheduled celery task for event "{}" processing and routing'.format(event['name']))
        except ValueError:
            logger.error('Could not encode event "{}"'.format(event['name']))
