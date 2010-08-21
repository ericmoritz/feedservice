import pymongo
from flask import (Flask, json, Response, request, abort)
import feedparser
from datetime import datetime
import time
from dateutil import tz
import os

app = Flask(__name__)
app.config.from_object("feedservice.default_settings")

if "FEEDSERVICE_SETTINGS" in os.environ:
    app.config.from_envvar("FEEDSERVICE_SETTINGS")

class FeedDB(object):
    def __init__(self, coll):
        self.coll = coll
        self.coll.ensure_index("feedurl")
        self.coll.ensure_index("timestamp")        

    def remove(self, feedurl):
        self.coll.remove({'feedurl': feedurl})
        
    def download(self, feedurl, etag=None):
        result = feedparser.parse(feedurl, etag=etag)
        
        def entry_gen(entries):
            for entry in entries:
                for key,val in entry.iteritems():
                    if type(val) == time.struct_time:
                        entry[key] = tuple(val)
                yield entry

        result['entries'] = list(entry_gen(result['entries']))

        return {'feedurl': feedurl, 'result': result,
                'timestamp': datetime.now(tz.tzutc())}

    def refresh(self, feedurl, etag=None):
        doc = self.download(feedurl, etag=etag)

        # If the feed's HTTP status was 200, store it
        if doc['result']['status'] == 200:
            app.logger.info("Storing feed %s" % feedurl)
            self.coll.update({'feedurl': doc['feedurl']},
                             doc,
                             upsert=True)
        return doc

    def get(self, feedurl):
        # Look for the doc in the collection
        doc = self.coll.find_one({'feedurl': feedurl})

        # If the doc is not found,
        if doc is None:
            app.logger.info("Feed %s not found, refreshing" % feedurl)
            # download the document
            doc = self.refresh(feedurl)
        
        return doc

con = pymongo.Connection(**app.config['MONGO_CONNECTION'])
mdb = getattr(con, app.config['MONGO_DATABASE'])
coll = getattr(mdb, app.config['MONGO_COLLECTION'])
feeddb = FeedDB(coll)

@app.route("/feed/")
def read():
    feedurl = request.args.get("q")
    callback = request.args.get("callback")
    refresh = request.args.get("refresh")

    if not feedurl:
        abort(404)

    if refresh:
        data = feeddb.refresh(feedurl)
    else:
        data = feeddb.get(feedurl)

    jsonstr = json.dumps(data, default=unicode)

    if callback:
        return "%s(%s)" % (callback, jsonstr)
    else:
        return jsonstr

    
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000, debug=True)

