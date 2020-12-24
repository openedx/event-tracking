"""
Strategies for locating contexts.  Allows for arbitrarily complex caching
and context differentiation strategies.

All context locators must implement a `get` method that returns an
`OrderedDict`-like object.
"""


from collections import OrderedDict
import threading


class DefaultContextLocator:
    """
    One-to-one mapping between contexts and trackers.  Every tracker will
    get a new context instance and it will always be returned by this
    locator.
    """

    def __init__(self):
        self.context = OrderedDict()

    def get(self):
        """Get a reference to the context."""
        return self.context


class ThreadLocalContextLocator:
    """
    Returns a different context depending on the thread that the locator
    was called from.  Thus, contexts can be isolated from one another
    on thread boundaries.

    Note that this makes use of `threading.local(),`  which is typically
    monkey-patched by alternative python concurrency frameworks (like `gevent`).

    Calls to `threading.local()` are delayed until first usage in order to
    give the third-party concurrency libraries an opportunity to monkey monkey
    patch it.
    """

    def __init__(self):
        self.thread_local_data = None

    def get(self):
        """Return a reference to a thread-specific context"""
        if not self.thread_local_data:
            self.thread_local_data = threading.local()

        if not hasattr(self.thread_local_data, 'context'):
            self.thread_local_data.context = OrderedDict()

        return self.thread_local_data.context
