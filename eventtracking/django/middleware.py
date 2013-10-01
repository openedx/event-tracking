"""Middleware that can be included to add context to tracked events."""

from __future__ import absolute_import

from contextlib import contextmanager
import re
import logging

from eventtracking import tracker

from django.conf import settings


logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


@contextmanager
def failures_only_in_debug():
    """
    Raises an error only when the Django setting DEBUG evaluates to True.

    Otherwise it simply logs the exception information and swallows the error.
    """
    try:
        yield
    except Exception:  # pylint: disable=broad-except
        if not getattr(settings, 'DEBUG', False):
            logger.warn('Exception raised in safe block.  Swallowing the error.', exc_info=True)
        else:
            raise


class TrackRequestContextMiddleware(object):
    """
    Adds a bunch of data pulled out of the request to the tracker context.
    Any application code (middleware, views etc) that execute after this
    middleware will include a bunch of information from the request in the
    context of any events they emit.
    """

    CONTEXT_NAME = 'django.context'

    def process_request(self, request):
        """Adds request variables to the Django tracker context."""

        with failures_only_in_debug():
            context = {
                'session': self.get_session_key(request),
                'user_primary_key': self.get_user_primary_key(request),
                'username': self.get_username(request)
            }
            header_context_key_map = {
                'REMOTE_ADDR': 'ip',
                'SERVER_NAME': 'host',
                'HTTP_USER_AGENT': 'agent',
                'PATH_INFO': 'path'
            }
            for header_name, context_key in header_context_key_map.iteritems():
                context[context_key] = request.META.get(header_name, '')

            tracker.get_tracker().enter_context(self.CONTEXT_NAME, context)

    def get_session_key(self, request):
        """Gets the Django session key from the request or an empty string if it isn't found"""
        try:
            return request.session.session_key
        except AttributeError:
            return ''

    def get_user_primary_key(self, request):
        """Gets the primary key of the logged in Django user"""
        try:
            return request.user.pk
        except AttributeError:
            return ''

    def get_username(self, request):
        """Gets the username of the logged in Django user"""
        try:
            return request.user.username
        except AttributeError:
            return ''

    def process_response(self, request, response):  # pylint: disable=unused-argument
        """Remove the request variable context from the tracker context stack"""
        with failures_only_in_debug():
            try:
                tracker.get_tracker().exit_context(self.CONTEXT_NAME)
            except KeyError:
                # If an error occurred processing some other middleware it is possible
                # this method could be called without process_request having been
                # called, in that case, don't raise an exception here.
                pass

        return response


class TrackRequestMiddleware(object):
    """
    Track all requests processed by Django.

    Supported Settings::

        `TRACKING_IGNORE_URL_PATTERNS`: A list of regular expressions that are executed
            on `request.path_info`, if any of them matches then no event will be emitted
            for the request.  Defaults to `[]`.

        `TRACKING_HTTP_REQUEST_EVENT_TYPE`: The event type for the events emitted on
            every request.  Defaults to "http.request."

    Example event::

        {
            "event_type": "http.request"
            # ...
            "data": {
                "method": "GET",
                "query": {
                    "arbitrary_get_parameter_name": "arbitrary_get_parameter_value",
                    # ... (all GET parameters will be included here)
                },
                "body": {
                    "arbitrary_post_parameter_name": "arbitrary_post_parameter_value",
                    # ... (all POST parameters will be included here)
                }
            }
        }
    """
    def process_response(self, request, response):
        """Emit an event for every request"""
        with failures_only_in_debug():
            if not self._should_process_request(request):
                return response

            event_type = getattr(settings, 'TRACKING_HTTP_REQUEST_EVENT_TYPE', 'http.request')

            event = {
                'method': request.method,
                'query': self._remove_sensitive_request_variables(request.GET),
                'body': self._remove_sensitive_request_variables(request.POST)
            }
            tracker.emit(event_type, event)

        return response

    def _remove_sensitive_request_variables(self, variable_dict):
        """Remove passwords and other sensitive data from the dictionary"""
        cleaned_dict = dict()
        for key, value in variable_dict.iteritems():
            if 'password' in key:
                value = ''
            cleaned_dict[key] = value

        return cleaned_dict

    def _should_process_request(self, request):
        """Ignore requests for paths that match a set of ignored patterns"""
        ignored_url_patterns = getattr(settings, 'TRACKING_IGNORE_URL_PATTERNS', [])
        for pattern in ignored_url_patterns:
            # Note we are explicitly relying on python's internal caching of
            # compiled regular expressions here.
            if re.match(pattern, request.path_info):
                return False
        return True
