import urlparse
import datetime
from smap.driver import SmapDriver
from smap.util import periodicSequentialCall
from smap.contrib import dtutil

class Scheduler(SmapDriver):
    def setup(self, opts):
        self.connect(opts)
        self.rate = float(opts.get('Rate', 1))
        self.day_map = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
    def start(self):
        periodicSequentialCall(self.read).start(self.rate)

    def read(self):
        c = self.MongoDatabase.master_schedule
        master_sched = c.find_one({})
        self.now = datetime.datetime.now() 
        day = self.day_map[self.now.weekday()]

        global_sched_type = master_sched[day]
        global_sched = self.get_schedule(global_sched_type)
        current_period = self.get_current_period(global_sched)

        # actuate me
        print current_period['points']

    def get_schedule(self, sched_type):
        c = self.MongoDatabase.schedules
        return c.find_one({'name': sched_type})
 
    def get_current_period(self, sched):
        prev_start = datetime.time(0,0,0)
        for p in sched['periods']:
            hour, minute = p['start'].split(':')
            start = datetime.time(int(hour), int(minute), 0)
            if self.now.time() > start and start > prev_start:
              cur_period = p
              prev_start = start
        return cur_period

    def connect(self, opts):
        from pymongo import MongoClient
        from pymongo.errors import ConnectionFailure as MongoConnectionFailure
        try:
            u = urlparse.urlparse(opts.get('MongoUrl'))
            url, port = u.netloc.split(':')
            self.MongoClient = MongoClient(url, int(port))
        except MongoConnectionFailure:
            return False
        self.MongoDatabase = getattr(self.MongoClient, 
            opts.get('MongoDatabaseName', 'meteor'))
        return True
