"""
Filter out events by comparing event names with the provided regular expressions.
"""
import re
from logging import getLogger

from eventtracking.processors.exceptions import EventEmissionExit
from eventtracking.exceptions import ImproperlyConfigured


logger = getLogger(__name__)

ALLOWLIST = 'allowlist'
BLOCKLIST = 'blocklist'


class RegexFilter:
    """
    Filter out events by comparing event names with the provided regular expressions.
    """

    def __init__(self, filter_type=ALLOWLIST, regular_expressions=None):
        self.regular_expressions = frozenset(regular_expressions or [])
        self.compiled_expressions = self._compile_regular_expressions()
        self.filter_type = filter_type
        self._validate_filter_type()

    def __call__(self, event):
        is_a_match = self._event_matches_filter(event['name'])

        if (
            (is_a_match and self.filter_type == ALLOWLIST) or
            (not is_a_match and self.filter_type == BLOCKLIST)
        ):
            return event

        raise EventEmissionExit()

    def _validate_filter_type(self):
        """
        Validate that the filter type is either `allowlist` or `blocklist`

        Raises:
            ImproperlyConfigured
        """
        if self.filter_type not in (ALLOWLIST, BLOCKLIST):
            logger.error(
                'Unsupported filter type {} is set. Allowed types are only {} and {}.'.format(
                    self.filter_type,
                    ALLOWLIST,
                    BLOCKLIST
                ))
            raise ImproperlyConfigured('Invalid filter type is configured')

    def _compile_regular_expressions(self):
        """
        Compile and validate every regular expression in the list.
        Throws on invalid regex.

        Returns:
            list<compiled re>
        """
        expressions_list = self.regular_expressions

        invalid_regex_expressions = []
        compiled_regex_expressions = []

        for exp in expressions_list:
            try:
                compiled = re.compile(exp)
                compiled_regex_expressions.append(compiled)
            except re.error:
                invalid_regex_expressions.append(exp)

        if invalid_regex_expressions:
            logger.error('The following invalid regular expressions are configured'
                         'for setting "ASYNC_ROUTING_BACKENDS_FILTERS": {}'.format(invalid_regex_expressions))
            raise ImproperlyConfigured('Invalid Regular Expressions are configured.')

        return compiled_regex_expressions

    def _event_matches_filter(self, event_name):
        """
        Determine if event name matches any of the regular expressions.

        Arguments:
            event_name (str):   name of the event

        Returns:
            bool
        """
        for expression in self.compiled_expressions:
            if expression.match(event_name):
                return True
        return False
