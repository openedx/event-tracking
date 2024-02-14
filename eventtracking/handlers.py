"""
This module contains the handlers for signals emitted by the analytics app.
"""
import json
import logging

from django.dispatch import receiver
from openedx_events.analytics.signals import TRACKING_EVENT_EMITTED
from openedx_events.tooling import SIGNAL_PROCESSED_FROM_EVENT_BUS

from eventtracking.backends.event_bus import EventBusRoutingBackend
from eventtracking.processors.exceptions import EventEmissionExit
from eventtracking.tracker import get_tracker

logger = logging.getLogger(__name__)


@receiver(TRACKING_EVENT_EMITTED)
def send_tracking_log_to_backends(
    sender, signal, **kwargs
):  # pylint: disable=unused-argument
    """
    Listen for the TRACKING_EVENT_EMITTED signal and send the event to the enabled backends.

    The process is the following:

    1. Unserialize the tracking log from the signal.
    2. Get the tracker instance to get the enabled backends (mongo, event_bus, logger, etc).
    3. Get the event bus backends that are the interested in the signals (multiple can be configured).
    4. Transform the event with the configured processors.
    5. Send the transformed event to the different event bus backends.

    This allows us to only send the tracking log to the event bus once and the event bus will send
    the transformed event to the different configured backends.
    """
    if not kwargs.get(SIGNAL_PROCESSED_FROM_EVENT_BUS, False):
        logger.debug("Event received from a non-event bus backend, skipping...")
        return
    tracking_log = kwargs.get("tracking_log")

    event = {
        "name": tracking_log.name,
        "timestamp": tracking_log.timestamp,
        "data": json.loads(tracking_log.data),
        "context": json.loads(tracking_log.context),
    }

    tracker = get_tracker()

    engines = {
        name: engine
        for name, engine in tracker.backends.items()
        if isinstance(engine, EventBusRoutingBackend)
    }
    for name, engine in engines.items():
        try:
            processed_event = engine.process_event(event)
            logger.info('Successfully processed event "{}"'.format(event["name"]))
            engine.send_to_backends(processed_event.copy())
        except EventEmissionExit:
            logger.info("[EventEmissionExit] skipping event {}".format(event["name"]))
