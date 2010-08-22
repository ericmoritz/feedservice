import pymongo
import feedparser
import time
from dateutil import tz
from datetime import datetime
from datetime import timedelta
import logging

logger = logging.getLogger("feedservice.backends.mongodb")

class FeedDB(object):
    def __init__(self, config):
        con = pymongo.Connection(**config['MONGO_CONNECTION'])
        mdb = getattr(con, config['MONGO_DATABASE'])
        self.config = config
        self.coll = getattr(mdb, config['MONGO_COLLECTION'])
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
            logger.info("Storing feed %s" % feedurl)
            self.coll.update({'feedurl': doc['feedurl']},
                             doc,
                             upsert=True)
        return doc

    def get(self, feedurl):
        # Look for the doc in the collection
        doc = self.coll.find_one({'feedurl': feedurl})

        # If the doc is not found,
        if doc is None:
            logger.info("Feed %s not found, refreshing" % feedurl)
            # download the document
            doc = self.refresh(feedurl)
        
        return doc

    def update_stale_feeds(self):
        """Returns a generator of stale documents"""

        d = timedelta(seconds=self.config['OLDAGE'])
        old_age = datetime.now(tz.tzutc()) - d

        c = self.coll.find({'timestamp': {'$lt': old_age}})

        count = c.count()
        logger.info("Found %s feeds older than %s" % (count, old_age))        

        for doc in c:
            etag = doc['result'].get('etag')
            logger.info("Updating %s" % doc['feedurl'])
            doc = self.refresh(doc['feedurl'], etag=etag)

            # If the HTTP from the refresh is not 200, update the timestamp
            # so we won't fetch it again for another period
            status = doc['result']['status'] 
            if status != 200:
                logger.info("Feed status not 200, %s," % status +
                                 " delaying next update")

                spec = {'feedurl': doc['feedurl']}
                update = {'timestamp': {'$set': datetime.now(tz.tzutc())}}
                self.coll.update(spec, update)

            
