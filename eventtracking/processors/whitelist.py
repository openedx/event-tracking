"""Filter out events whose names aren't on a pre-configured whitelist"""

from eventtracking.processors.exceptions import EventEmissionExit


class WhitelistProcessor(object):
    """

    Filter out events whose names aren't on a pre-configured whitelist.

    `whitelist` is an iterable containing event names that should be allowed to pass.
    """

    def __init__(self, **kwargs):
        self.whitelist = frozenset(kwargs.get('whitelist', []))

    def __call__(self, event):
        if event['name'] not in self.whitelist:
            raise EventEmissionExit()
        else:
            return event
