"""
A django specific tracker.
"""
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

    def __init__(
            self,
            backends_settings_name=DJANGO_BACKEND_SETTING_NAME,
            processors_settings_name=DJANGO_PROCESSOR_SETTING_NAME
    ):
        backends = self.create_backends_from_settings(backends_settings_name)
        processors = self.create_processors_from_settings(processors_settings_name)
        super().__init__(backends, ThreadLocalContextLocator(), processors)

    def create_backends_from_settings(self, settings_name):
        """
        Expects the Django setting with `settings_name` (default: "EVENT_TRACKING_BACKENDS")
        to be defined and point to a dictionary of backend engine configurations.

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
        config = getattr(settings, settings_name, {})

        backends = self._instantiate_objects(config)

        return backends

    def _instantiate_objects(self, node):
        """
        Recursively traverse a structure to identify dictionaries that represent objects that need to be instantiated

        Traverse all values of all dictionaries and all elements of all lists to identify dictionaries that contain the
        special "ENGINE" key which indicates that a class of that type should be instantiated and passed all key-value
        pairs found in the sibling "OPTIONS" dictionary as keyword arguments.

        For example::

            tree = {
                'a': {
                    'b': {
                        'first_obj': {
                            'ENGINE': 'mypackage.mymodule.Clazz',
                            'OPTIONS': {
                                'size': 10,
                                'foo': 'bar'
                            }
                        }
                    },
                    'c': [
                        {
                            'ENGINE': 'mypackage.mymodule.Clazz2',
                            'OPTIONS': {
                                'more_objects': {
                                    'd': {'ENGINE': 'mypackage.foo.Bar'}
                                }
                            }
                        }
                    ]
                }
            }
            root = self._instantiate_objects(tree)

        That structure of dicts, lists, and strings will end up with (this example assumes that all keyword arguments to
        constructors were saved as attributes of the same name):

        assert type(root['a']['b']['first_obj']) == <type 'mypackage.mymodule.Clazz'>
        assert root['a']['b']['first_obj'].size == 10
        assert root['a']['b']['first_obj'].foo == 'bar'
        assert type(root['a']['c'][0]) == <type 'mypackage.mymodule.Clazz2'>
        assert type(root['a']['c'][0].more_objects['d']) == <type 'mypackage.foo.Bar'>
        """
        result = node
        if isinstance(node, dict):
            if 'ENGINE' in node:
                result = self._instantiate_from_dict(node)
            else:
                result = {}
                for key, value in node.items():
                    result[key] = self._instantiate_objects(value)
        elif isinstance(node, list):
            result = []
            for child in node:
                result.append(self._instantiate_objects(child))

        return result

    def _instantiate_from_dict(self, values):
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
        except (ValueError, AttributeError, TypeError, ImportError) as error:
            raise ValueError('Cannot find class %s' % name) from error

        options = self._instantiate_objects(options)
        return cls(**options)

    def create_processors_from_settings(self, settings_name):
        """
        Expects the Django setting with `settings_name` (default: "EVENT_TRACKING_PROCESSORS")
        to be defined and point to a list of backend engine configurations.

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
        config = getattr(settings, settings_name, [])

        processors = self._instantiate_objects(config)

        return processors


def override_default_tracker():
    """Sets the default tracker to a DjangoTracker"""
    if getattr(settings, DJANGO_ENABLED_SETTING_NAME, False):
        tracker.register_tracker(DjangoTracker())
