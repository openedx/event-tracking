"""Custom exceptions that are raised by this package"""


class EventEmissionExit(Exception):
    """
    Raising this exception indicates that no further processing of the event should occur and it should be dropped.

    This should only be raised by processors.
    """


class NoTransformerImplemented(Exception):
    """
    Raise this exception when there is no transformer implemented
    for an event.
    """


class NoBackendEnabled(Exception):
    """
    Raise this exception when there is no backend enabled
    for an event.
    """
