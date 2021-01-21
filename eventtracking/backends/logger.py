"""Event tracker backend that saves events to a python logger."""


from datetime import datetime
from datetime import date
import logging
import json

from pytz import UTC

MAX_EVENT_SIZE = 1024  # 1 KB


class LoggerBackend:
    """
    Event tracker backend that uses a python logger.

    Events are logged to the INFO level as JSON strings.
    """

    def __init__(self, **kwargs):
        """
        Event tracker backend that uses a python logger.

        `name` is an identifier for the logger, which should have
            been configured using the default python mechanisms.
        """
        name = kwargs.get('name', None)
        self.max_event_size = kwargs.get('max_event_size', MAX_EVENT_SIZE)
        self.event_logger = logging.getLogger(name)
        level = kwargs.get('level', 'info')
        self.log = getattr(self.event_logger, level.lower())

    def send(self, event):
        """Send the event to the standard python logger"""
        event_str = json.dumps(event, cls=DateTimeJSONEncoder)

        # TODO: do something smarter than simply dropping the event on
        # the floor.
        if self.max_event_size is None or len(event_str) <= self.max_event_size:
            self.log(event_str)


class DateTimeJSONEncoder(json.JSONEncoder):
    """JSON encoder aware of datetime.datetime and datetime.date objects"""

    def default(self, obj):  # pylint: disable=arguments-differ
        """
        Serialize datetime and date objects of iso format.

        datatime objects are converted to UTC.
        """

        if isinstance(obj, datetime):
            if obj.tzinfo is None:
                # Localize to UTC naive datetime objects
                obj = UTC.localize(obj)  # pylint: disable=no-value-for-parameter
            else:
                # Convert to UTC datetime objects from other timezones
                obj = obj.astimezone(UTC)
            return obj.isoformat()
        elif isinstance(obj, date):
            return obj.isoformat()

        return super().default(obj)
