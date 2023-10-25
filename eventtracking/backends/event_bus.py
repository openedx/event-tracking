"""Event tracker backend that emits events to the event-bus."""
import json

from openedx_events.analytics.data import TrackingLogData
from openedx_events.analytics.signals import TRACKING_EVENT_EMITTED

from eventtracking.backends.routing import RoutingBackend
from eventtracking.config import SEND_TRACKING_EVENT_EMITTED_SIGNAL
from openedx_events.data import EventsMetadata
from openedx_events.event_bus import get_producer
from attrs import asdict
import logging

logger = logging.getLogger(__name__)

EVENT_BUS_SOURCE = "openedx/eventtracking"

class EventBusRoutingBackend(RoutingBackend):
    """
    Event tracker backend that emits an Open edX public signal.
    """

    def send(self, event):
        """
        Emit the TRACKING_EVENT_EMITTED Open edX public signal to allow
        other apps to listen for tracking events.
        """
        if not SEND_TRACKING_EVENT_EMITTED_SIGNAL.is_enabled():
            return

        data = json.dumps(event.get("data"))
        context = json.dumps(event.get("context"))

        tracking_log=TrackingLogData(
            name=event.get("name"),
            timestamp=event.get("timestamp"),
            data=data,
            context=context,
        )

        logger.info(f"Sending tracking event emitted signal for event for {tracking_log.name}")
        get_producer().send(
            signal=TRACKING_EVENT_EMITTED,
            topic="analytics",
            event_key_field="tracking_log.name",
            event_data={"tracking_log": tracking_log},
            event_metadata=generate_signal_metadata()
        )


def generate_signal_metadata():
    """
    Generate the metadata for the signal with a custom source.
    """
    metadata = TRACKING_EVENT_EMITTED.generate_signal_metadata()
    medata_dict = asdict(metadata)
    medata_dict["source"] = EVENT_BUS_SOURCE
    metadata = EventsMetadata(**medata_dict)
    return metadata
