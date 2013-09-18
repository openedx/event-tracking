"""
Track application events.  Supports persisting events to multiple backends.

Best Practices:
* It is recommended that event types are namespaced using dot notation to
  avoid naming collisions, similar to DNS names.  For example:
  org.edx.video.stop, edu.mit.audio.stop
* Avoid using event type names that may cause collisions.  The burden is
  on the analyst to decide whether your event is equivalent to another
  and should be grouped accordingly etc.
* Do not emit events that you don't own.  This could negatively impact
  the analysis of the event stream.  If you suspect your event is
  equivalent to another, say so in your documenation, and the analyst
  can decide whether or not to group them.
"""
from datetime import datetime
import logging


LOG = logging.getLogger(__name__)
BACKENDS = []


def event(event_type, data=None):
    """
    Emit an event annotated with the UTC time when this function was called.

    :event_type: A unique identification string for an event that has already been registered.
    :data: A dictionary mapping field names to the value to include in the event.  Note that all values provided must be serializable.

    """
    full_event = {
        'event_type': event_type,
        'timestamp': datetime.utcnow(),
        'data': data or {}
    }

    for backend in BACKENDS:
        try:
            backend.event(full_event)
        except Exception:  # pylint: disable=W0703
            LOG.exception(
                'Unable to commit event to backend: {0}'.format(backend)
            )
