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

from __future__ import absolute_import

from datetime import datetime
from collections import defaultdict
import logging

from pytz import UTC

__all__ = ['get_tracker', 'event']


LOG = logging.getLogger(__name__)


class Tracker(object):
    """
    Track application events.  Holds references to a set of backends that will
    be used to persist any events that are emitted.
    """
    def __init__(self):
        self.backends = {}

    def get_backend(self, name):
        """Gets the backend that was configured with `name`"""
        return self.backends[name]

    def add_backend(self, name, backend):
        """Adds a backend to the tracker"""
        self.backends[name] = backend

    def clear_backends(self):
        """Remove all backends from the tracker"""
        self.backends = {}

    def event(self, event_type, data=None):
        """
        Emit an event annotated with the UTC time when this function was called.

        `event_type` is a unique identification string for an event that has
            already been registered.
        `data` is a dictionary mapping field names to the value to include in the event.
            Note that all values provided must be serializable.

        """
        full_event = {
            'event_type': event_type,
            'timestamp': datetime.now(UTC),
            'data': data or {}
        }

        for name, backend in self.backends.iteritems():
            try:
                backend.send(full_event)
            except Exception:  # pylint: disable=broad-except
                LOG.exception(
                    'Unable to send event to backend: {0}'.format(name)
                )


GLOBAL_TRACKERS = defaultdict(Tracker)
GLOBAL_TRACKERS['__default__'] = Tracker()


def get_tracker(name=None):
    """Gets a named tracker.  Defaults to the default global tracker."""
    name = name or '__default__'
    return GLOBAL_TRACKERS[name]


def event(event_type, data=None):
    """Calls `Tracker.event` on the default global tracker"""
    return get_tracker().event(event_type, data=data)
