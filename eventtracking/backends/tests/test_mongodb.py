"""Unit tests for the Mongo backend"""

from unittest import TestCase
from unittest.mock import patch
from unittest.mock import sentinel

from pymongo.errors import PyMongoError
from bson.errors import BSONError

from eventtracking.backends.mongodb import MongoBackend


class TestMongoBackend(TestCase):
    """Unit tests for the Mongo backend"""

    def setUp(self):
        super().setUp()
        self.mongo_patcher = patch('eventtracking.backends.mongodb.MongoClient')
        self.addCleanup(self.mongo_patcher.stop)
        self.mongo_patcher.start()

        self.backend = MongoBackend()

    def test_mongo_backend(self):
        events = [{'test': 1}, {'test': 2}]

        self.backend.send(events[0])
        self.backend.send(events[1])

        # Check if we inserted events into the database

        calls = self.backend.collection.insert.mock_calls

        self.assertEqual(len(calls), 2)

        # Unpack the arguments and check if the events were used
        # as the first argument to collection.insert

        def first_argument(call):
            """Extract the first argument from a `mock.call`"""
            _, args, _ = call
            return args[0]

        self.assertEqual(events[0], first_argument(calls[0]))
        self.assertEqual(events[1], first_argument(calls[1]))

    def test_authentication_settings(self):
        backend = MongoBackend(user=sentinel.user, password=sentinel.password)
        backend.database.authenticate.assert_called_once_with(sentinel.user, sentinel.password)

    def test_mongo_pymongo_insertion_error(self):
        self.backend.collection.insert.side_effect = PyMongoError

        self.backend.send({'test': 1})
        # Ensure this error is caught

    def test_mongo_bson_insertion_error(self):
        self.backend.collection.insert.side_effect = BSONError

        self.backend.send({'test': 1})
        # Ensure this error is caught
