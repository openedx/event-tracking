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


from contextlib import contextmanager
from datetime import datetime
import logging

from pytz import UTC

from eventtracking.locator import DefaultContextLocator
from eventtracking.backends.routing import RoutingBackend

UNKNOWN_EVENT_TYPE = 'unknown'
DEFAULT_TRACKER_NAME = 'default'
TRACKERS = {}
LOG = logging.getLogger(__name__)


class Tracker:
    """
    Track application events.  Holds references to a set of backends that will
    be used to persist any events that are emitted.
    """
    def __init__(self, backends=None, context_locator=None, processors=None):
        self.routing_backend = RoutingBackend(backends=backends, processors=processors)
        self.context_locator = context_locator or DefaultContextLocator()

    @property
    def located_context(self):
        """
        The thread local context for this tracker.
        """
        return self.context_locator.get()

    def get_backend(self, name):
        """Gets the backend that was configured with `name`"""
        return self.backends[name]

    @property
    def processors(self):
        """The list of registered processors"""
        return self.routing_backend.processors

    @property
    def backends(self):
        """The dictionary of registered backends"""
        return self.routing_backend.backends

    def emit(self, name=None, data=None):
        """
        Emit an event annotated with the UTC time when this function was called.

        `name` is a unique identification string for an event that has
            already been registered.
        `data` is a dictionary mapping field names to the value to include in the event.
            Note that all values provided must be serializable.

        """
        event = {
            'name': name or UNKNOWN_EVENT_TYPE,
            'timestamp': datetime.now(UTC),
            'data': data or {},
            'context': self.resolve_context()
        }

        self.routing_backend.send(event)

    def resolve_context(self):
        """
        Create a new dictionary that corresponds to the union of all of the
        contexts that have been entered but not exited at this point.
        """
        merged = dict()
        for context in self.located_context.values():
            merged.update(context)
        return merged

    def enter_context(self, name, ctx):
        """
        Enter a named context.  Any events emitted after calling this
        method will contain all of the key-value pairs included in `ctx`
        unless overridden by a context that is entered after this call.
        """
        self.located_context[name] = ctx

    def exit_context(self, name):
        """
        Exit a named context.  This will remove all key-value pairs
        associated with this context from any events emitted after it
        is removed.
        """
        del self.located_context[name]

    @contextmanager
    def context(self, name, ctx):
        """
        Execute the block with the given context applied.  This manager
        ensures that the context is removed even if an exception is raised
        within the context.
        """
        self.enter_context(name, ctx)
        try:
            yield
        finally:
            self.exit_context(name)


def register_tracker(tracker, name=DEFAULT_TRACKER_NAME):
    """
    Makes a tracker globally accessible.  Providing no `name` parameter
    allows you to register the global default tracker that will be used
    by subsequent calls to `tracker.emit`.
    """
    TRACKERS[name] = tracker


def get_tracker(name=DEFAULT_TRACKER_NAME):
    """
    Gets a named tracker.  Defaults to the default global tracker.  Raises
    a `KeyError` if no such tracker has been registered by previously calling
    `register_tracker`.
    """
    return TRACKERS[name]


def emit(name=None, data=None):
    """Calls `Tracker.emit` on the default global tracker"""
    return get_tracker().emit(name=name, data=data)
