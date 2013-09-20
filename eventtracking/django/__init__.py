"""A django specific tracker"""

from __future__ import absolute_import

from importlib import import_module

from django.conf import settings

from eventtracking import track

__all__ = ['track']


DJANGO_TRACKER_NAME = 'django'


def configure_from_settings(tracker_name=None, setting_name=None):
    """
    Configure event tracking.  Expects the Django setting "TRACKING_BACKENDS"
    to be defined and point to a dictionary of backend engines.

    Example::

        TRACKING_BACKENDS = {
            'default': {
                'ENGINE': 'some.arbitrary.Backend',
                'OPTIONS': {
                    'endpoint': 'http://something/event'
                }
            },
            'another_engine': {
                'ENGINE': 'some.arbitrary.OtherBackend',
                'OPTIONS': {
                    'user': 'foo'
                }
            },
        }
    """
    config = getattr(settings, setting_name or 'TRACKING_BACKENDS', {})

    tracker = get_tracker(tracker_name)
    tracker.clear_backends()

    for name, values in config.iteritems():
        # Ignore empty values to turn-off default tracker backends
        if values and 'ENGINE' in values:
            engine = values['ENGINE']
            options = values.get('OPTIONS', {})
            backend = _instantiate_backend_from_name(engine, options)
            tracker.add_backend(name, backend)

    return tracker


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
    except (ValueError, AttributeError, TypeError, ImportError):
        raise ValueError('Cannot find event track backend %s' % name)

    backend = cls(**options)
    if not hasattr(backend, 'send') or not callable(backend.send):
        raise ValueError('Backend %s does not have a callable "send" method.' % name)

    return backend


def get_tracker(name=None):
    """Get the Django specific tracker"""
    return track.get_tracker(name or DJANGO_TRACKER_NAME)


# Configure the default tracker using the default settings
configure_from_settings()