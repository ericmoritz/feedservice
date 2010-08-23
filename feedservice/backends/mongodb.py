import pymongo
import time
from dateutil import tz
from datetime import datetime
from datetime import timedelta
import logging
from feedservice.backends import base

logger = logging.getLogger("feedservice.backends.mongodb")

class FeedDB(base.BaseFeedDB):
    def __init__(self, config):
        con = pymongo.Connection(**config['MONGO_CONNECTION'])
        mdb = getattr(con, config['MONGO_DATABASE'])
        self.config = config
        self.coll = getattr(mdb, config['MONGO_COLLECTION'])
        self.coll.ensure_index("feedurl")
        self.coll.ensure_index("timestamp")        

    def remove(self, feedurl):
        self.coll.remove({'feedurl': feedurl})

    def update(self, doc):
        self.coll.update({'feedurl': doc['feedurl']},
                          doc,
                          upsert=True)

    def fetch(self, feedurl):
        return self.coll.find_one({'feedurl': feedurl})

    def find_stale(self):

        d = timedelta(seconds=self.config['OLDAGE'])
        old_age = datetime.now(tz.tzutc()) - d

        c = self.coll.find({'timestamp': {'$lt': old_age}})

        count = c.count()
        logger.info("Found %s feeds older than %s" % (count, old_age))        

        return c
