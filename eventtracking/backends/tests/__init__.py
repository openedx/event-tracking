"""
Helper classes for backend tests
"""

from unittest import TestCase
from contextlib import contextmanager
import time
import os
import random
import string


class InMemoryBackend:
    """A backend that simply stores all events in memory"""

    def __init__(self):
        super().__init__()
        self.events = []

    def send(self, event):
        """Store the event in a list"""
        self.events.append(event)


class IntegrationTestCase(TestCase):
    """
    Tests the integration between a backend and any external systems
    it makes use of.
    """

    # This is equivalent to decorating all subclasses with attr('integration')
    # which allows us to selectively run integration tests.
    integration = 1


class PerformanceTestCase(TestCase):
    """
    Reads parameters from the following environment variables:

    * EVENT_TRACKING_PERF_EVENTS - Number of events to send to the backend
    * EVENT_TRACKING_PERF_PAYLOAD_SIZE - Approximate size (in bytes) of a
      payload field to include in every event.
    * EVENT_TRACKING_PERF_THRESHOLD_SECONDS - Fail the test if it takes
      longer than this number of seconds to save all of the events.
    """

    # This is equivalent to decorating all subclasses with attr('performance')
    performance = 1

    # pylint: disable=invalid-envvar-default
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.num_events = int(os.getenv('EVENT_TRACKING_PERF_EVENTS', 20000))
        self.payload_size = int(os.getenv('EVENT_TRACKING_PERF_PAYLOAD_SIZE', 600))
        self.random_payload = ''.join(random.choice(string.ascii_letters) for _ in range(self.payload_size))
        self.threshold = float(os.getenv('EVENT_TRACKING_PERF_THRESHOLD_SECONDS', 1.75))

    @contextmanager
    def assert_execution_time_less_than_threshold(self):
        """
        Times the execution of the block within the context and raises an
        `AssertionError` if it is longer than `self.threshold`
        """
        start_time = time.time()
        yield
        elapsed_time = time.time() - start_time

        print('')
        print(f'Elapsed Time: {elapsed_time} seconds')
        print(f'Threshold: {self.threshold} seconds')
        print(f'Number of Events: {self.num_events}')
        print(f'Payload Size: {self.payload_size} bytes')
        print('Events per second: {}'.format(self.num_events / elapsed_time))

        if self.threshold >= 0:
            self.assertLessEqual(elapsed_time, self.threshold)
