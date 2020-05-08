"""Custom exceptions that are raised by this package"""


class EventEmissionExit(Exception):
    """
    Raising this exception indicates that no further processing of the event should occur and it should be dropped.

    This should only be raised by processors.
    """
