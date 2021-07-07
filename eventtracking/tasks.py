"""
Celery tasks
"""
import json

from celery import shared_task
from celery.utils.log import get_task_logger

from eventtracking.tracker import get_tracker
from eventtracking.processors.exceptions import EventEmissionExit


logger = get_task_logger(__name__)
# Maximum number of retries before giving up on rounting event
MAX_RETRIES = 3
# Number of seconds after task is retried
COUNTDOWN = 30


@shared_task(bind=True)
def send_event(self, backend_name, json_event):
    """
    Send event to configured top-level backend asynchronously.

    Load the backend with name `backend_name` and use it to process and send
    the event to configured nested backends.

    WARNING: Do not use this task directly! It is intended for use
    only by the AsyncRoutingBackend, since it is implemented with the
    following assumptions:

    - That the top-level processors have already been run on the event
    - That the named backend is a RoutingBackend (or descendent)

    Arguments:
        backend_name (str):    name of the backend to use
        json_event (str)  :    JSON encoded event
    """
    event = json.loads(json_event)
    tracker = get_tracker()
    backend = tracker.backends[backend_name]

    # Reimplements `RoutingBackend.send()` logic so that the event
    # doesn't get sent via celery again.
    #
    # `AsyncRoutingBackend.send()` should probably be changed to add
    # an `immediate=False` kwarg and call the super method to perform
    # immediate processing when `immediate=True`.

    try:
        processed_event = backend.process_event(event)
        logger.info('Successfully processed event "{}"'.format(event['name']))

        for __, backend in backend.backends.items():
            backend.send(processed_event.copy())

    except EventEmissionExit:
        logger.info('[EventEmissionExit] skipping event {}'.format(event['name']))
        return
    except Exception as exc:
        logger.exception(
            '[send_event] Failed to send event [%s] with backend [%s], [%s]',
            event['name'], backend_name, exc
        )
        raise self.retry(exc=exc, countdown=COUNTDOWN, max_retries=MAX_RETRIES)
