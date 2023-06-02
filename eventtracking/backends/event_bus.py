"""Event tracker backend that emits events to the event-bus."""
from openedx_events.analytics.signals import TRACKING_EVENT_EMITTED
from openedx_events.analytics.data import TrackingLogData

class EventBusRoutingBackend:
    """
    Event tracker backend that emits an Open edX public signal.
    """

    def __init__(self, **kwargs):
        """
        Event tracker backend that emits an Open edX public signal.
        """

    def send(self, event):
        """
        Emit the TRACKING_EVENT_EMITTED Open edX public signal to allow
        other apps to listen for tracking events.
        """
        # .. event_implemented_name: TRACKING_EVENT_EMITTED
        TRACKING_EVENT_EMITTED.send_event(
            tracking_log=TrackingLogData(
                name=event.get('name'),
                timestamp=event.get('timestamp'),
                data=event.get('data'),
                context=event.get('context')
            )
        )
