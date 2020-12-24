"""
Runs invasive tests to ensure that the tracking system can communicate with
an actual MongoDB instance.
"""


from datetime import datetime
from uuid import uuid4

from pytz import UTC

from eventtracking.backends.mongodb import MongoBackend
from eventtracking.backends.tests import InMemoryBackend, IntegrationTestCase
from eventtracking.tracker import Tracker


class TestMongoIntegration(IntegrationTestCase):
    """
    Makes use of a real MongoDB instance to ensure the backend is wired up
    properly to the external system.  These tests require a mongodb instance
    to be running on localhost listening on the default port.
    """

    def setUp(self):
        super().setUp()
        self.database_name = 'test_eventtracking_' + str(uuid4())
        self.mongo_backend = MongoBackend(database=self.database_name)
        self.memory_backend = InMemoryBackend()
        self.tracker = Tracker({
            'mongo': self.mongo_backend,
            'mem': self.memory_backend
        })

    def tearDown(self):
        self.mongo_backend.connection.drop_database(self.database_name)
        super().tearDown()

    def test_sequential_events(self):
        now = datetime.now(UTC)
        for i in range(10):
            self.tracker.emit('org.test.user.login', {
                'username': 'tester',
                'user_id': 10,
                'email': 'tester@eventtracking.org',
                'sequence': i,
                'current_time': now
            })

        # Ensure MongoDB has finished writing out the events before we
        # run our query.
        self.mongo_backend.connection.fsync()

        mem_events = {}
        for event in self.memory_backend.events:
            mem_events[event['data']['sequence']] = event
        self.assertEqual(len(mem_events), 10)

        cursor = self.mongo_backend.collection.find()
        self.assertEqual(cursor.count(), 10)

        for event in cursor:
            mem_event = mem_events[event['data']['sequence']]
            mem_event['_id'] = event['_id']
            if self.are_results_equal(mem_event, event):
                del mem_events[event['data']['sequence']]
        self.assertEqual(len(mem_events), 0)

    def are_results_equal(self, left, right):
        """
        Ensure two events are equivalent.

        We use a bit of special logic here when comparing timestamps since
        MongoDB apparently only stores millisecond precision timestamps.
        Thus, when comparing we ignore the datetime.millisecond property.
        """
        for event in [left, right]:
            self.remove_microseconds_from_timestamps(event)

        return left == right

    def remove_microseconds_from_timestamps(self, event):
        """Truncate the microseconds from the event timestamp"""
        event['timestamp'] = event['timestamp'].replace(microsecond=0)
        event['data']['current_time'] = event['data']['current_time'].replace(microsecond=0)
