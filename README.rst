feedservice
============
feedservice provides a little feed caching service to ensure that external
feeds will be fetched in a timely manner.

feedservice uses MongoDB_ and has two components, a web service and a 
janitorial process.

feedservice uses Mark Pilgrim's excellent feedparser_ module to ensure that
feeds are always readible and formatted in a well documented format.

.. _MongoDB: http://www.mongodb.org/
.. _feedparser: http://www.feedparser.org/


Web Service
------------
The `feedservice.webservice.app` is a standard WSGI app built using Flask_.
You can deploy it using gunicorn_::

    gunicorn feedservice.webserice:app

.. _gunicorn: http://gunicorn.org/
.. _Flask: http://flask.pocoo.org/

The feedservice URL is at `/feed`.  The URL has the following parameters

    q
       The feed's URL

    refresh
       The feed will be reloaded live when this parameter is present

    callback
       This is a JSONP callback if you want to use this service from 
       browser.  Word of warning, this service is meant to be a
       internal serice, using it as a JSONP service might be insecure.

The response of the feed URL is a JSON document.  This JSON document contains
three keys::

    feedurl
       The feed's URL
   
    timestamp
       The date and time in UTC when the feed was last fetched

    result
       The result of feedparser ran on the feed




Janitor Process
----------------
A script is installed called `feedjanitor`, this runs in the background
and updates stale feeds.


Settings
---------
There are a few settings that may or may not need to be changed.  The defaults
will work fine with a insecure mongodb running on your localhost on the
standard port

    MONGO_CONNECTION
       A dictionary of the kwargs for the pymongo.Connection object.  Default:
       {'host': 'localhost'}

    MONGO_DATABASE
       The database to store the feeds into. Default: "feedservice"

    MONGO_COLLECTION
       The collection to store the feeds into. Default: "feedservice"

    OLDAGE
       The number of seconds at which a feed becomes stale.  Default: 180
    

To change any of these defaults, create a python module and point to it in
a environment variable called, "FEEDSERVICE_SETTINGS"

