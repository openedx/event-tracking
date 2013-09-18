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
from importlib import import_module
import inspect
import logging

from eventtracking.backends import BaseBackend


__all__ = ['configure', 'event']


LOG = logging.getLogger(__name__)
BACKENDS = {}


def configure(config):
    """
    Configure event tracking.  `config` is expected to be a dictionary of backend engines.

    Example::

        config = {
            'default': {
                'ENGINE': 'some.arbitrary.Backend',
                'OPTIONS': {
                    'endpoint': 'http://something/event'
                }
            },
            'anoter_engine': {
                'ENGINE': 'some.arbitrary.OtherBackend',
                'OPTIONS': {
                    'user': 'foo'
                }
            },
        }
    """
    BACKENDS.clear()

    for name, values in config.iteritems():
        # Ignore empty values to turn-off default tracker backends
        if values and 'ENGINE' in values:
            engine = values['ENGINE']
            options = values.get('OPTIONS', {})
            BACKENDS[name] = _instantiate_backend_from_name(engine, options)


def _instantiate_backend_from_name(name, options):
    """
    Instantiate an event tracker backend from the full module path to
    the backend class. Useful when setting backends from configuration
    files.

    """
    # Parse backend name

    parts = name.split('.')
    module_name = '.'.join(parts[:-1])
    class_name = parts[-1]

    # Get and verify the backend class

    try:
        module = import_module(module_name)
        cls = getattr(module, class_name)
        if not inspect.isclass(cls) or not issubclass(cls, BaseBackend):
            raise TypeError
    except (ValueError, AttributeError, TypeError, ImportError):
        raise ValueError('Cannot find event track backend %s' % name)

    backend = cls(**options)

    return backend


def event(event_type, data=None):
    """
    Emit an event annotated with the UTC time when this function was called.

    `event_type` is a unique identification string for an event that has already been registered.
    `data` is a dictionary mapping field names to the value to include in the event.
        Note that all values provided must be serializable.

    """
    full_event = {
        'event_type': event_type,
        'timestamp': datetime.utcnow(),
        'data': data or {}
    }

    for name, backend in BACKENDS.iteritems():
        try:
            backend.send(full_event)
        except Exception:  # pylint: disable=broad-except
            LOG.exception(
                'Unable to send event to backend: {0}'.format(name)
            )
