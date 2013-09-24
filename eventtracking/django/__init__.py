"""A django specific tracker"""

from __future__ import absolute_import

from importlib import import_module

from django.conf import settings

from eventtracking import track
from eventtracking.track import Tracker


DJANGO_TRACKER_NAME = 'django'
DJANGO_SETTING_NAME = 'TRACKING_BACKENDS'


class DjangoTracker(Tracker):
    """
    A `eventtracking.track.Tracker` that constructs its backends from
    Django settings.
    """

    def __init__(self, setting_name=DJANGO_SETTING_NAME):
        backends = self.create_backends_from_settings(setting_name)
        super(DjangoTracker, self).__init__(backends)

    def create_backends_from_settings(self, setting_name=DJANGO_SETTING_NAME):
        """
        Expects the Django setting `setting_name` (defaults to
        "TRACKING_BACKENDS") to be defined and point to a dictionary of
        backend engine configurations.

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
        config = getattr(settings, setting_name, {})

        backends = {}

        for name, values in config.iteritems():
            # Ignore empty values to turn-off default tracker backends
            if values and 'ENGINE' in values:
                engine = values['ENGINE']
                options = values.get('OPTIONS', {})
                backend = self.instantiate_backend_from_name(engine, options)
                backends[name] = backend

        return backends

    def instantiate_backend_from_name(self, name, options):
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


def get_tracker(name=DJANGO_TRACKER_NAME):
    """Get the Django specific tracker"""
    return track.get_tracker(name)


# Configure the default tracker using the default settings
track.register_tracker(DjangoTracker(), DJANGO_TRACKER_NAME)
