"""
Runs invasive tests to ensure that the tracking system can communicate with
an actual MongoDB instance.
"""

from __future__ import absolute_import

from uuid import uuid4

from eventtracking.backends.tests import IntegrationTestCase
from eventtracking.backends.tests import InMemoryBackend
from eventtracking.backends.mongodb import MongoBackend
from eventtracking.track import Tracker


class TestMongoIntegration(IntegrationTestCase):
    """
    Makes use of a real MongoDB instance to ensure the backend is wired up
    properly to the external system.
    """

    def setUp(self):
        self.database_name = 'test_eventtracking_' + str(uuid4())
        self.tracker = Tracker()
        self.mongo_backend = MongoBackend(database=self.database_name)
        self.tracker.add_backend('mongo', self.mongo_backend)
        self.memory_backend = InMemoryBackend()
        self.tracker.add_backend('mem', self.memory_backend)

    def tearDown(self):
        self.mongo_backend.connection.drop_database(self.database_name)

    def test_sequential_events(self):
        for i in range(10):
            self.tracker.event('org.test.user.login', {
                'username': 'tester',
                'user_id': 10,
                'email': 'tester@eventtracking.org',
                'sequence': i
            })

        # Ensure MongoDB has finished writing out the events before we
        # run our query.
        self.mongo_backend.connection.fsync()

        cursor = self.mongo_backend.collection.find()
        self.assertEquals(cursor.count(), 10)
        for i, event in enumerate(cursor):
            mem_event = self.memory_backend.events[i]
            mem_event['_id'] = event['_id']
            self.assert_events_are_equal(mem_event, event)

    def assert_events_are_equal(self, left, right):
        """
        Ensure two events are equivalent.

        We use a bit of special logic here when comparing timestamps since
        MongoDB apparently only stores millisecond precision timestamps.
        Thus, when comparing we ignore the datetime.millisecond property.
        """
        for event in [left, right]:
            self.remove_microseconds_from_timestamp(event)

        self.assertEquals(left, right)

    def remove_microseconds_from_timestamp(self, event):
        """Truncate the microseconds from the event timestamp"""
        event['timestamp'] = event['timestamp'].replace(microsecond=0)
