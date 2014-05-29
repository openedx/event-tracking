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

.. |build-status| image:: https://api.travis-ci.org/edx/event-tracking.png?branch=master 
   :target: https://travis-ci.org/edx/event-tracking
