"""
New AppConfig for Django 1.8
"""
from django.apps import AppConfig


class EventTrackingConfig(AppConfig):
    """
    Django 1.8 requires unique app labels and only uses the characters to the right of the
    last period in the string. .django was not specific enough.
    """

    name = 'eventtracking.django'
    label = 'eventtracking_django'

    def ready(self):
        """
        Initialize django specific tracker.
        """
        super().ready()
        # pylint: disable=import-outside-toplevel
        from eventtracking.django.django_tracker import override_default_tracker
        override_default_tracker()
