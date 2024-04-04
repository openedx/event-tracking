"""Event tracker backend that emits events to the event-bus."""

import json
import logging
from datetime import datetime

from django.conf import settings
from openedx_events.analytics.data import TrackingLogData
from openedx_events.analytics.signals import TRACKING_EVENT_EMITTED

from eventtracking.backends.logger import DateTimeJSONEncoder
from eventtracking.backends.routing import RoutingBackend
from eventtracking.config import SEND_TRACKING_EVENT_EMITTED_SIGNAL

logger = logging.getLogger(__name__)


class EventBusRoutingBackend(RoutingBackend):
    """
    Event tracker backend for the event bus.
    """

    def __init__(self, processors=None, backends=None, backend_name=''):
        self.backend_name = backend_name
        super().__init__(processors=processors, backends=backends)

    def send(self, event):
        """
        Send the tracking log event to the event bus by emitting the
        TRACKING_EVENT_EMITTED signal using custom metadata.
        """
        if not SEND_TRACKING_EVENT_EMITTED_SIGNAL.is_enabled():
            return

        name = event.get("name")

        if name not in getattr(settings, "EVENT_BUS_TRACKING_LOGS", []):
            return

        data = json.dumps(event.get("data"), cls=DateTimeJSONEncoder)
        context = json.dumps(event.get("context"), cls=DateTimeJSONEncoder)

        timestamp = event.get("timestamp")

        if isinstance(timestamp, str):
            timestamp = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%f%z")

        tracking_log = TrackingLogData(
            name=event.get("name"),
            timestamp=timestamp,
            data=data,
            context=context,
        )
        TRACKING_EVENT_EMITTED.send_event(tracking_log=tracking_log)

        logger.info(f"Tracking log {tracking_log.name} emitted to the event bus.")
