import pymongo
import feedparser
import time
from dateutil import tz
from datetime import datetime
from datetime import timedelta
import logging

logger = logging.getLogger("feedservice.backends.base")

class BaseFeedDB(object):

    def remove(self, feedurl):
        """Removes documents found at this feedurl"""
        raise NotImplementedError()

    def update(self, doc):
        """Update the document"""
        raise NotImplementedError()

    def fetch(self, feedurl):
        """Find one document found at the feedurl"""
        raise NotImplementedError()

    def find_stale(self):
        """Return a generator of stale documents."""
        raise NotImplementedError()


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
            self.update(doc)

        return doc

    def get(self, feedurl):
        # Look for the doc in the collection
        doc = self.fetch(feedurl)

        # If the doc is not found,
        if doc is None:
            logger.info("Feed %s not found, refreshing" % feedurl)
            # download the document
            doc = self.refresh(feedurl)
        
        return doc

    def update_stale_feeds(self):
        """Updates stale feeds"""
        c = self.find_stale()

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

                doc['timestamp'] = datetime.now(tz.tzutc())

                self.update(doc)

            
