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
        
        today_sched = self.get_schedule(master_sched[day])
        current_period = self.get_current_period(today_sched)

        if not current_period:
            # carry over from yesterday
            yest = self.day_map[self.now.weekday()-1]
            yest_sched = self.get_schedule(master_sched[yest])
            temp_latest = datetime.time(0,0,0)
            for p in yest_sched['periods']:
                hour, minute = p['start'].split(':')
                start = datetime.time(int(hour), int(minute), 0)
                if start > temp_latest:
                    current_period = p
                    temp_latest = start

        schedule_points = current_period['points']

        # get the relevant points in openbas
        paths = [x['path'] for x in schedule_points]
        control_points = self.get_control_points(paths)
        for x in control_points:
            print x
 
    def get_control_points(self, paths):
        # use $or and $regex
        regex_list = [{'Path': { '$regex': '.*%s$' % p }} for p in paths]
        clause = {'$or': regex_list} 
        return self.MongoDatabase.points.find(clause)

    def get_schedule(self, sched_type):
        c = self.MongoDatabase.schedules
        return c.find_one({'name': sched_type})
 
    def get_current_period(self, sched):
        cur_period = None
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
