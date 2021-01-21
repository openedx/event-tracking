"""Route events to processors and backends"""


import logging
from collections import OrderedDict
from copy import deepcopy

from eventtracking.processors.exceptions import EventEmissionExit


LOG = logging.getLogger(__name__)


class RoutingBackend:
    """

    Route events to the appropriate backends.

    A routing backend has two types of components:

    1) Processors - These are run sequentially, processing the output of the previous processor. If you had three
       processors [a, b, c], the output of the processing step would be `c(b(a(event)))`. Note that for performance
       reasons, the processor is able to actually mutate the event dictionary in-place. Event dictionaries may be large
       and highly nested, so creating multiple copies could be problematic. A processor can also choose to prevent the
       event from being emitted by raising `EventEmissionExit`. Doing so will prevent any subsequent processors from
       running and prevent the event from being sent to the backends. Any other exception raised by a processor will be
       logged and swallowed, subsequent processors will execute and the event will be emitted.
    2) Backends - Backends are intended to not mutate the event and each receive the same event data. They are not
       chained like processors. Once an event has been processed by the processor chain, it is passed to each backend in
       the order that they were registered. Backends typically persist the event in some way, either by sending it
       to an external system or saving it to disk. They are called synchronously and in sequence, so a long running
       backend will block other backends until it is done persisting the event. Note that you can register another
       `RoutingBackend` as a backend of a `RoutingBackend`, allowing for arbitrary processing trees.

    `backends` is a collection that supports iteration over its items using `iteritems()`. The keys are expected to be
        sortable and the values are expected to expose a `send(event)` method that will be called for each event. Each
        backend in this collection is registered in order sorted alphanumeric ascending by key.
    `processors` is an iterable of callables.

    Raises a `ValueError` if any of the provided backends do not have a callable "send" attribute or any of the
        processors are not callable.
    """

    def __init__(self, backends=None, processors=None):
        self.backends = OrderedDict()
        self.processors = []

        if backends is not None:
            for name in sorted(backends.keys()):
                self.register_backend(name, backends[name])

        if processors is not None:
            for processor in processors:
                self.register_processor(processor)

    def register_backend(self, name, backend):
        """
        Register a new backend that will be called for each processed event.

        Note that backends are called in the order that they are registered.
        """
        if not hasattr(backend, 'send') or not callable(backend.send):
            raise ValueError('Backend %s does not have a callable "send" method.' % backend.__class__.__name__)

        self.backends[name] = backend

    def register_processor(self, processor):
        """
        Register a new processor.

        Note that processors are called in the order that they are registered.
        """
        if not callable(processor):
            raise ValueError('Processor %s is not callable.' % processor.__class__.__name__)

        self.processors.append(processor)

    def send(self, event):
        """
        Process the event using all registered processors and send it to all registered backends.

        Logs and swallows all `Exception`.
        """
        event = deepcopy(event)

        try:
            processed_event = self.process_event(event)
        except EventEmissionExit:
            return
        else:
            self.send_to_backends(processed_event)

    def process_event(self, event):
        """

        Executes all event processors on the event in order.

        `event` is a nested dictionary that represents the event.

        Logs and swallows all `Exception` except `EventEmissionExit` which is re-raised if it is raised by a processor.

        Returns the modified event.
        """

        if len(self.processors) == 0:
            return event

        processed_event = event

        for processor in self.processors:
            try:
                modified_event = processor(processed_event)
                if modified_event is not None:
                    processed_event = modified_event
            except EventEmissionExit:
                raise
            except Exception:  # pylint: disable=broad-except
                LOG.exception(
                    'Failed to execute processor: %s', str(processor)
                )

        return processed_event

    def send_to_backends(self, event):
        """
        Sends the event to all registered backends.

        Logs and swallows all `Exception`.
        """

        for name, backend in self.backends.items():
            try:
                backend.send(event)
            except Exception:  # pylint: disable=broad-except
                LOG.exception(
                    'Unable to send event to backend: %s', name
                )
