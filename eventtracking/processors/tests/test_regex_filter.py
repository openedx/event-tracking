"""
Test the RegexFilter processor.
"""
from unittest.mock import sentinel
import ddt
from django.test import TestCase

from eventtracking.processors.exceptions import EventEmissionExit
from eventtracking.exceptions import ImproperlyConfigured
from eventtracking.processors.regex_filter import RegexFilter, ALLOWLIST, BLOCKLIST


@ddt.ddt
class TestRegexFilterProcessor(TestCase):
    """
    Test the RegexFilter processor.
    """

    def setUp(self):
        super().setUp()
        self.sample_event = {
            'name': str(sentinel.name),
            'event_type': 'edx.test.event',
            'time': '2020-01-01T12:12:12.000000+00:00',
            'event': {
                'key': 'value'
            },
            'session': '0000'
        }

    def test_with_invalid_configurations(self):
        with self.assertRaises(ImproperlyConfigured):
            RegexFilter(filter_type='INVALID_TYPE', regular_expressions=[])

        with self.assertRaises(ImproperlyConfigured):
            RegexFilter(filter_type=ALLOWLIST, regular_expressions=['***'])

    @ddt.data(
        (ALLOWLIST, ['sentinel.name', 'any'], True),
        (ALLOWLIST, ['not_matching', 'NOT_MATCHING'], False),
        (ALLOWLIST, [''], True),
        (ALLOWLIST, [], False),
        (BLOCKLIST, ['sentinel.name', 'any'], False),
        (BLOCKLIST, ['not_matching', 'NOT_MATCHING'], True),
        (BLOCKLIST, [''], False),
        (BLOCKLIST, [], True),
    )
    @ddt.unpack
    def test_with_multiple_regex(self, filter_type, expressions, should_pass):
        regex_filter = RegexFilter(filter_type=filter_type, regular_expressions=expressions)

        if should_pass:
            self.assertEqual(regex_filter(self.sample_event), self.sample_event)
        else:
            with self.assertRaises(EventEmissionExit):
                regex_filter(self.sample_event)
