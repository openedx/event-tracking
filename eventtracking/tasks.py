"""
Celery tasks
"""
import json

from celery.utils.log import get_task_logger
from celery import shared_task

from eventtracking.tracker import get_tracker
from eventtracking.processors.exceptions import EventEmissionExit


logger = get_task_logger(__name__)


@shared_task(name='eventtracking.tasks.send_event')
def send_event(backend_name, json_event):
    """
    Send event to configured backends asynchronously.

    Load the backend with name `backend_name` and use it to process and send
    the event to configured nested backends.

    Arguments:
        backend_name (str):    name of the backend to use
        json_event (str)  :    JSON encoded event
    """
    event = json.loads(json_event)
    tracker = get_tracker()
    backend = tracker.backends[backend_name]

    try:
        processed_event = backend.process_event(event)
        logger.info('Successfully processed event "{}"'.format(event['name']))

    except EventEmissionExit:
        logger.info('[EventEmissionExit] skipping event {}'.format(event['name']))
        return

    for name, backend in backend.backends.items():
        logger.info('Sending processed event "{}" to backend {}.'.format(event['name'], name))
        backend.send(processed_event.copy())
