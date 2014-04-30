"""A django specific tracker"""

from __future__ import absolute_import

from importlib import import_module

from django.conf import settings

from eventtracking import tracker
from eventtracking.tracker import Tracker
from eventtracking.locator import ThreadLocalContextLocator


DJANGO_BACKEND_SETTING_NAME = 'EVENT_TRACKING_BACKENDS'
DJANGO_PROCESSOR_SETTING_NAME = 'EVENT_TRACKING_PROCESSORS'
DJANGO_ENABLED_SETTING_NAME = 'EVENT_TRACKING_ENABLED'


class DjangoTracker(Tracker):
    """
    A `eventtracking.tracker.Tracker` that constructs its backends from
    Django settings.
    """

    def __init__(self):
        backends = self.create_backends_from_settings()
        processors = self.create_processors_from_settings()
        super(DjangoTracker, self).__init__(backends, ThreadLocalContextLocator(), processors)

    def create_backends_from_settings(self):
        """
        Expects the Django setting "EVENT_TRACKING_BACKENDS" to be defined and point
        to a dictionary of backend engine configurations.

        Example::

            EVENT_TRACKING_BACKENDS = {
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
        config = getattr(settings, DJANGO_BACKEND_SETTING_NAME, {})

        backends = {}

        for name, values in config.iteritems():
            # Ignore empty values to turn-off default tracker backends
            if values and 'ENGINE' in values:
                backend = self.instantiate_from_dict(values)
                backends[name] = backend

        return backends

    def instantiate_from_dict(self, values):
        """
        Constructs an object given a dictionary containing an "ENGINE" key
        which contains the full module path to the class, and an "OPTIONS"
        key which contains a dictionary that will be passed in to the
        constructor as keyword args.
        """

        name = values['ENGINE']
        options = values.get('OPTIONS', {})

        # Parse the name
        parts = name.split('.')
        module_name = '.'.join(parts[:-1])
        class_name = parts[-1]

        # Get the class
        try:
            module = import_module(module_name)
            cls = getattr(module, class_name)
        except (ValueError, AttributeError, TypeError, ImportError):
            raise ValueError('Cannot find class %s' % name)

        return cls(**options)

    def create_processors_from_settings(self):
        """
        Expects the Django setting "EVENT_TRACKING_PROCESSORS" to be defined and
        point to a list of backend engine configurations.

        Example::

            EVENT_TRACKING_PROCESSORS = [
                {
                    'ENGINE': 'some.arbitrary.Processor'
                },
                {
                    'ENGINE': 'some.arbitrary.OtherProcessor',
                    'OPTIONS': {
                        'user': 'foo'
                    }
                },
            ]
        """
        config = getattr(settings, DJANGO_PROCESSOR_SETTING_NAME, [])

        processors = []
        for values in config:
            # Ignore empty values to turn-off default tracker backends
            if values and 'ENGINE' in values:
                processors.append(self.instantiate_from_dict(values))

        return processors


def override_default_tracker():
    """Sets the default tracker to a DjangoTracker"""
    if getattr(settings, DJANGO_ENABLED_SETTING_NAME, False):
        tracker.register_tracker(DjangoTracker())


override_default_tracker()
