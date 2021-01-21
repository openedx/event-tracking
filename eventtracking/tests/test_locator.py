"""Test context locators."""


from unittest.mock import sentinel
from unittest import TestCase
import threading

from eventtracking import locator


class TestThreadLocalContextLocator(TestCase):
    """Test context locators."""

    def test_multithreaded_context(self):
        self.locator = locator.ThreadLocalContextLocator()  # pylint: disable=attribute-defined-outside-init

        # Events emitted from the parent thread should have this context
        context = {sentinel.context_key: sentinel.context_value}

        # Events emitted from the child thread should have this context
        thread_context = {sentinel.thread_key: sentinel.thread_value}

        # Set once the child thread has setup its context
        thread_in_context = threading.Event()
        # Set once the parent has emitted its event
        parent_sent_event = threading.Event()

        def worker():
            """A simulated child thread"""
            # Setup a context in this thread.  This should not inherit the parent thread context!
            self.locator.get()['child'] = thread_context

            # At this point both the parent and child threads have entered their contexts, but
            # the child thread should only "see" the context it setup.
            self.assertEqual(self.locator.get(), {'child': thread_context})

            # Notify the parent that the child has setup its context.  At this point both the
            # parent and the child have entered their own contexts.
            thread_in_context.set()
            # Wait for the parent to emit its event
            parent_sent_event.wait()

            del self.locator.get()['child']

            self.assertEqual(self.locator.get(), {})

        self.locator.get()['parent'] = context

        other_thread = threading.Thread(target=worker)
        other_thread.start()

        # Wait for the thread to setup its context.
        thread_in_context.wait()

        # At this point both the parent and child threads have entered their contexts, but
        # the parent thread should only "see" the context it setup.
        self.assertEqual(self.locator.get(), {'parent': context})

        # Notify the thread that it can send its event and exit
        parent_sent_event.set()
        other_thread.join()

        del self.locator.get()['parent']

        self.assertEqual(self.locator.get(), {})
