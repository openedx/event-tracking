"""Test the whitelist processor"""

from __future__ import absolute_import

from unittest import TestCase

from mock import sentinel

from eventtracking.processors.exceptions import EventEmissionExit
from eventtracking.processors.whitelist import WhitelistProcessor


class TestWhitelistProcessor(TestCase):
    """Test the whitelist processor"""

    def test_filtering_out(self):
        whitelist = WhitelistProcessor(whitelist=[sentinel.allowed_event])
        with self.assertRaises(EventEmissionExit):
            whitelist({'name': sentinel.not_allowed_event})

    def test_allowed_event(self):
        whitelist = WhitelistProcessor(whitelist=[sentinel.allowed_event])
        self.assert_event_passed_through(whitelist, {'name': sentinel.allowed_event})

    def assert_event_passed_through(self, whitelist, event):
        """Assert that the whitelist allowed the event processing to procede"""
        self.assertEquals(whitelist(event), event)

    def test_empty_whitelist(self):
        whitelist = WhitelistProcessor(whitelist=[])
        with self.assertRaises(EventEmissionExit):
            whitelist({'name': sentinel.not_allowed_event})

    def test_multi_entry_whitelist(self):
        whitelist = WhitelistProcessor(whitelist=[sentinel.allowed_event, sentinel.another_event])
        with self.assertRaises(EventEmissionExit):
            whitelist({'name': sentinel.not_allowed_event})

        self.assert_event_passed_through(whitelist, {'name': sentinel.allowed_event})
        self.assert_event_passed_through(whitelist, {'name': sentinel.another_event})
