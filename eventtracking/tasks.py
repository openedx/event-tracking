"""
Celery tasks
"""

from celery.utils.log import get_task_logger
from celery import shared_task
from edx_django_utils.monitoring import set_code_owner_attribute_from_module
from eventtracking.tracker import get_tracker
from eventtracking.processors.exceptions import (
    NoBackendEnabled,
    NoTransformerImplemented,
)

logger = get_task_logger(__name__)
# Maximum number of retries before giving up on rounting event
MAX_RETRIES = 3
# Number of seconds after task is retried
COUNTDOWN = 30


@shared_task(bind=True)
def send_event(self, backend_name, processed_event):
    """
    Send event to configured top-level backend asynchronously.

    WARNING: Do not use this task directly! It is intended for use
    only by the AsyncRoutingBackend, since it is implemented with the
    following assumptions:

    - That the top-level processors have already been run on the event
    - That the named backend is a RoutingBackend (or descendent)

    Arguments:
        self (dict): task
        backend_name (str):  name of the backend to use
        processed_event (dict): Processed event dict
    """
    set_code_owner_attribute_from_module(self.__module__)
    try:
        tracker = get_tracker()
        backend = tracker.backends[backend_name]
        backend.send_to_backends(processed_event.copy())

    except (NoTransformerImplemented, NoBackendEnabled) as exc:
        logger.info(
            '[send_event] Failed to send event [%s] with backend [%s], [%s]',
            processed_event['name'], backend_name, exc
        )

    except Exception as exc:
        logger.exception(
            '[send_event] Failed to send event [%s] with backend [%s], [%s]',
            processed_event['name'], backend_name, repr(exc)
        )
        raise self.retry(exc=exc, countdown=COUNTDOWN, max_retries=MAX_RETRIES)
