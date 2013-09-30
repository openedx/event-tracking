Part of `edX code`__.

__ http://code.edx.org/

event-tracking
==============

.. image:: https://api.travis-ci.org/edx/event-tracking.png?branch=master
    :target: https://travis-ci.org/edx/event-tracking

This is a system for tracking events.  It is designed to support pluggable
backends for persisting the event data. When the application emits an event
each backend will be given an opportunity to save the event to stable storage.

It currently provides:

* Nested contexts - allows data to be injected into events even without
  having to pass around all of said data to every location where the events
  are emitted.
* Django integration - provide a Django app that allows events to easily be
  captured by web applications.

Example::

    from eventtracking import track

    tracker = track.get_tracker()
    tracker.enter_context('outer', {'user_id': 10938})
    tracker.emit('navigation.request', {'url': 'http://www.edx.org/some/path/1'})

    with tracker.context({'user_id': 11111, 'session_id': '2987lkjdyoioey'}):
        tracker.emit('navigation.request', {'url': 'http://www.edx.org/some/path/2'})

    tracker.emit('navigation.request', {'url': 'http://www.edx.org/some/path/3'})

    # The following list shows the contexts and data for the three events that
    # are emitted
    #  "context": { "user_id": 10938 },
             "data": { "url": "http://www.edx.org/some/path/1" }
    #  "context": { "user_id": 11111, "session_id": "2987lkjdyoioey" },
            "data": { "url": "http://www.edx.org/some/path/2" }
    #  "context": { "user_id": 10938 },
            "data": { "url": "http://www.edx.org/some/path/3" }

Roadmap
-------

In the very near future the following features are planned:

* Dynamic documentation and event metadata - allow event emitters to document
  the event types, and persist this documentation along with the events so
  that it can be referenced during analysis to provide context about what
  the event is and when it is emitted.


Documentation
-------------

Initial API docs can be found in the ``doc`` directory.

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
