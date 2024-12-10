"""Filter out events whose names aren't on a pre-configured whitelist"""


from eventtracking.processors.exceptions import EventEmissionExit


class NameWhitelistProcessor:
    """

    Filter out events whose names aren't on a pre-configured whitelist.

    `whitelist` is an iterable collection containing event names that should be allowed to pass.
    """

    def __init__(self, whitelist=None, **_kwargs):
        try:
            if isinstance(whitelist, str):
                raise TypeError

            self.whitelist = frozenset(whitelist)
        except TypeError as error:
            raise TypeError(
                'The NameWhitelistProcessor must be passed a collection of allowed names '
                'using the "whitelist" parameter'
            ) from error

    def __call__(self, event):
        """
        Filter out events whose names aren't on the whitelist.

        The event can be a single event or a list of events (when using event-routing-backends with batching enabled).
        """
        if isinstance(event, list):
            return [e for e in event if e['name'] in self.whitelist]
        elif event['name'] not in self.whitelist:
            raise EventEmissionExit()

        return event
