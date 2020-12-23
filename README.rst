Part of `edX code`__.

__ http://code.edx.org/

Event Tracking library |build-status|
=====================================

The ``event-tracking`` library tracks context-aware semi-structured system events.
It captures and stores events with nested data structures in order to truly
take advantage of schemaless data storage systems.

Key features:

* Multiple backends - define custom backends that can be used to persist
  your event data.
* Nested contexts - allows data to be injected into events even without
  having to pass around all of said data to every location where the events
  are emitted.
* Django integration - provides a Django app that allows context aware events
  to easily be captured by multi-threaded web applications.
* MongoDB integration - support writing events out to a mongo collection.

Example::

    from eventtracking import tracker

    tracker = tracker.get_tracker()
    tracker.enter_context('outer', {'user_id': 10938})
    tracker.emit('navigation.request', {'url': 'http://www.edx.org/some/path/1'})

    with tracker.context({'user_id': 11111, 'session_id': '2987lkjdyoioey'}):
        tracker.emit('navigation.request', {'url': 'http://www.edx.org/some/path/2'})

    tracker.emit(
        'address.create',
        {
            'name': 'foo',
            'address': {
                'postal_code': '90210',
                'country': 'United States'
            }
        }
    )

Running the above example produces the following events::

    {
        "name": "navigation.request",
        "timestamp": ...,
        "context": {
            "user_id": 10938
        },
        "data": {
            "url": "http://www.edx.org/some/path/1"
        }
    },
    {
        "name": "navigation.request",
        "timestamp": ...,
        "context": {
            "user_id": 11111,
            "session_id": "2987lkjdyoioey"
        },
        "data": {
            "url": "http://www.edx.org/some/path/2"
        }
    },
    {
        "name": "address.create",
        "timestamp": ...,
        "context": {
            "user_id": 10938
        },
        "data": {
            "name": "foo",
            "address": {
                "postal_code": "90210",
                "country": "United States"
            }
        }
    }


Configuration
-------------

Configuration for ``event-tracking`` takes the form of a tree of backends. When a ``Tracker`` is instantiated, it creates a root ``RoutingBackend`` object using the top-level backends and processors that are passed to it. (Or in the case of the ``DjangoTracker``, the backends and processors are constructed according to the appropriate Django settings.)

In this ``RoutingBackend``, each event is first passed through the chain of processors in series, and then distributed to each backend in turn. Theoretically, these backends might be the Mongo, Segment, or logger backends, but in practice these are wrapped by another layer of ``RoutingBackend``. This allows each one to have its own set of processors that are not shared with other backends, allowing independent filtering or event emit cancellation.


Asynchronous Routing
--------------------

Considering the volume of the events being generated, we would want to avoid
processing events in the main thread that could cause delays in response
depending upon the operations and event processors.

``event-tracking`` provides a solution for this i.e. ``AsyncRoutingBackend``.
It extends ``RoutingBackend`` but performs its operations asynchronously.

It can:

* Process event through the configured processors.
* If the event is processed successfully, pass it to the configured backends.

Handling the operations asynchronously would avoid overburdening the main thread
and pass the intensive processing tasks to celery workers.

**Limitations**: Although backends for ``RoutingBackend`` can be configured
at any level of ``EVENT_TRACKING_BACKENDS`` configuration tree,
``AsyncRoutingBackend`` only supports backends defined at the root level of
``EVENT_TRACKING_BACKENDS`` setting.  It is also only possible to use it
successfully from the default tracker.

An example configuration for ``AsyncRoutingBackend`` is provided below::

    EVENT_TRACKING_BACKENDS = {
        'caliper': {
            'ENGINE':  'eventtracking.backends.async_routing.AsyncRoutingBackend',
            'OPTIONS': {
                'backend_name': 'caliper',
                'processors': [
                    {
                        'ENGINE': 'eventtracking.processors.regex_filter.RegexFilter',
                        'OPTIONS':{
                            'filter_type': 'allowlist',
                            'regular_expressions': [
                                'edx.course.enrollment.activated',
                                'edx.course.enrollment.deactivated',
                            ]
                        }
                    }
                ],
                'backends': {
                    'caliper': {
                        'ENGINE': 'dummy.backend.engine',
                        'OPTIONS': {
                            ...
                        }
                    }
                },
            },
        },
        'tracking_logs': {
            ...
        }
        ...
    }


Roadmap
-------

In the very near future the following features are planned:

* Dynamic event documentation and event metadata - allow event emitters to
  document the event types, and persist this documentation along with the
  events so that it can be referenced during analysis to provide context
  about what the event is and when it is emitted.


Documentation
-------------

`Latest documentation <http://event-tracking.readthedocs.org/en/latest/>`_ (Hosted on Read the Docs)


License
-------

The code in this repository is licensed under version 3 of the AGPL unless
otherwise noted.

Please see ``LICENSE.txt`` for details.


How to Contribute
-----------------

Contributions are very welcome.

Please read `How To Contribute <https://github.com/edx/edx-platform/wiki/How-To-Contribute>`_ for details.

Reporting Security Issues
-------------------------

Please do not report security issues in public. Please email security@edx.org

Mailing List and IRC Channel
----------------------------

You can discuss this code on the `edx-code Google Group`__ or in the
``edx-code`` IRC channel on Freenode.

__ https://groups.google.com/forum/#!forum/edx-code

.. |build-status| image:: https://api.travis-ci.com/edx/event-tracking.svg?branch=master
   :target: https://travis-ci.com/edx/event-tracking
