"""Test the whitelist processor"""


from unittest import TestCase

from unittest.mock import sentinel

from eventtracking.processors.exceptions import EventEmissionExit
from eventtracking.processors.whitelist import NameWhitelistProcessor


class TestNameWhitelistProcessor(TestCase):
    """Test the whitelist processor"""

    def test_filtering_out(self):
        whitelist = NameWhitelistProcessor(whitelist=[sentinel.allowed_event])
        with self.assertRaises(EventEmissionExit):
            whitelist({'name': sentinel.not_allowed_event})

    def test_allowed_event(self):
        whitelist = NameWhitelistProcessor(whitelist=[sentinel.allowed_event])
        self.assert_event_passed_through(whitelist, {'name': sentinel.allowed_event})

    def assert_event_passed_through(self, whitelist, event):
        """Assert that the whitelist allowed the event processing to proceed"""
        self.assertEqual(whitelist(event), event)

    def test_empty_whitelist(self):
        whitelist = NameWhitelistProcessor(whitelist=[])
        with self.assertRaises(EventEmissionExit):
            whitelist({'name': sentinel.not_allowed_event})

    def test_multi_entry_whitelist(self):
        whitelist = NameWhitelistProcessor(whitelist=[sentinel.allowed_event, sentinel.another_event])
        with self.assertRaises(EventEmissionExit):
            whitelist({'name': sentinel.not_allowed_event})

        self.assert_event_passed_through(whitelist, {'name': sentinel.allowed_event})
        self.assert_event_passed_through(whitelist, {'name': sentinel.another_event})

    def test_no_whitelist_param(self):
        with self.assert_initialization_fails():
            NameWhitelistProcessor()

    def assert_initialization_fails(self):
        """Assert that the constructor raises the expected initialization exception"""
        return self.assertRaisesRegexp(  # pylint: disable=deprecated-method,useless-suppression
            TypeError, r'The NameWhitelistProcessor must be passed')

    def test_whitelist_param_not_iterable(self):
        with self.assert_initialization_fails():
            NameWhitelistProcessor(10)

    def test_whitelist_param_just_a_string(self):
        with self.assert_initialization_fails():
            NameWhitelistProcessor('foobar')

    def test_whitelist_param_is_none(self):
        with self.assert_initialization_fails():
            NameWhitelistProcessor(None)

    def test_initialize_with_set(self):
        self.assert_properly_configured(frozenset([sentinel.allowed_event]))

    def assert_properly_configured(self, allowed_names):
        """Assert that whitelist was configured properly by correctly passing and/or filtering events"""
        whitelist = NameWhitelistProcessor(whitelist=allowed_names)
        self.assert_event_passed_through(whitelist, {'name': sentinel.allowed_event})
        with self.assertRaises(EventEmissionExit):
            whitelist({'name': sentinel.not_allowed_event})

    def test_initialize_with_dict(self):
        self.assert_properly_configured({sentinel.allowed_event: sentinel.discarded})
