import urlparse
import json
import datetime
from twisted.internet import reactor

from smap.driver import SmapDriver
from smap.util import periodicSequentialCall

class Scheduler(SmapDriver):
    def setup(self, opts):
        self.schedule = self.load_schedule(opts.get('source'))
        self.is_master = opts.get('is_master').lower() == 'true'
        self.save_location = opts.get('saveto')

        if self.save_location is not None:
            self.save()

        self.set_metadata('/', {
            'Schedule/Name': self.schedule['name'],
            'Schedule/Description': self.schedule['description']
        })

        for point_name, point_desc in self.schedule['point descriptions'].items():
            timeseries_point = Scheduler._fix_point_name(point_name).encode('utf-8')
            self.add_timeseries(timeseries_point, point_desc['units'], data_type='double')
            self.set_metadata(timeseries_point, {
                'Schedule/Point/Name': point_name,
                'Schedule/Point/Description': point_desc['desc']
            })

        self.periods = self.schedule['periods']
        self.epochs = {}
        # index the schedule periods by the number of seconds from midnight
        for period in self.periods:
            seconds_since_midnight = Scheduler._convert_time_to_seconds(period['start'])
            self.epochs[seconds_since_midnight] = period

        # find most recent schedule
        now = Scheduler._current_time_as_seconds()
        self.nextEpoch = self.find_epoch_before_time(now)
        if self.nextEpoch is None: # if nothing before, find the next one to use
            self.nextEpoch = self.find_epoch_after_time(now)

    def start(self):
        self.push_epoch()

    def find_epoch_before_time(self, targettime):
        """
        Given a time that is the number of seconds since midnight of the current day,
        returns the epoch most recently before that
        """
        diffs = map(lambda x: x - targettime, self.epochs.keys())
        # find smallest difference less than 0 to find periods before
        diffsBefore = filter(lambda x: x < 0, diffs)
        if not len(diffsBefore):
            # nothing before, so take the max (from the previous day)
            return self.epochs.keys()[diffs.index(max(diffs))]
        return self.epochs.keys()[diffs.index(max(diffsBefore))]

    def find_epoch_after_time(self, targettime):
        """
        Given a time that is the number of seconds since midnight of the current day,
        returns the epoch most immediately after
        """
        diffs = map(lambda x: targettime - x, self.epochs.keys())
        # find smallest difference less than 0 to find periods before
        diffsAfter = filter(lambda x: x < 0, diffs)
        if not len(diffsAfter):
            # nothing after, so take the min (for the next day)
            return self.epochs.keys()[diffs.index(min(diffs))]
        return self.epochs.keys()[diffs.index(max(diffsAfter))]


    def push_epoch(self):
        """
        Iterates through the points for epoch self.nextEpoch and publishes them. Each epoch looks like
            {
                "name": "morning",
                "start": "7:30",
                "points": [
                    {
                        "name": "Heating Setpoint",
                        "value": 72
                    },
                    {
                        "name": "Cooling Setpoint",
                        "value": 83
                    }
                ]
            }
        Then, it schedules the next epoch to be pushed
        """
        print 'pushing', self.nextEpoch, self.epochs[self.nextEpoch]
        for point in self.epochs[self.nextEpoch]['points']:
            timeseries_point = Scheduler._fix_point_name(point['name']).encode('utf-8')
            self.add(timeseries_point, float(point['value']))
        self.nextEpoch = self.find_epoch_after_time(self.nextEpoch)
        print 'next epoch is',self.nextEpoch
        wait = Scheduler._get_time_til_epoch(self.nextEpoch)
        print self.nextEpoch
        print 'call later in', wait, 'seconds'
        reactor.callLater(wait, self.push_epoch)


    @staticmethod
    def _fix_point_name(name):
        """
        Transforms input name to url_safe for use as a timeseries, e.g.
        "Heating Setpoint" -> heating_setpoint
        """
        return '/' + name.lower().replace(' ','_')

    @staticmethod
    def _convert_time_to_seconds(timestring):
        """
        Takes a time schedule string, e.g. ("7:30" or "18:45:00"), and transforms
        into the number of seconds since midnight
        """
        chunks = timestring.split(":")
        if len(chunks) == 2:
            hour, minute = chunks
            second = 0
        elif len(chunks) == 3:
            hour, minute, second = chunks
        else:
            return 0 # can't parse
        hour, minute, second = int(hour), int(minute), int(second)
        return 1 * second + 60 * minute + 3600 * hour

    @staticmethod
    def _get_time_til_epoch(epoch):
        curTime = Scheduler._current_time_as_seconds()
        diff = epoch - curTime
        print 'diff',diff
        print 'cur', curTime
        print 'epoch', epoch
        if diff > 0:
            return diff
        else:
            return 24 * 3600 - curTime + epoch

    @staticmethod
    def _current_time_as_seconds():
        """
        Returns the current time as the number of seconds since midnight
        """
        now = datetime.datetime.now()
        return 1 * now.second + 60 * now.minute + 3600 * now.hour

    def load_schedule(self, source):
        """
        In order to make this slightly more general, we allow the source of the JSON-spec
        schedule to be specified as a URI. Mongo, HTTP and File URIs are supported, but
        we can easily imagine extending this to other databases or sources.
        """
        uri = urlparse.urlparse(source)
        scheme = uri.scheme.lower()
        if scheme == 'file':
            filename = uri.path[1:] # remove leading '/'
            sched = json.load(open(filename))
            return sched
        elif scheme == 'http':
            pass
            #import requests
            #sched = json.loads(requests.get(source).content)
            ##self.master_schedule = sched['master_schedule']
            #self.schedules = sched['schedules']

    def save(self):
        uri = urlparse.urlparse(self.save_location)
        scheme = uri.scheme.lower()
        if scheme == 'mongodb':
            from pymongo import MongoClient
            from pymongo.errors import ConnectionFailure as MongoConnectionFailure
            url, port = uri.netloc.split(':')
            db = uri.path[1:] # remove leading '/'
            client = MongoClient(url, int(port))
            db = client.xbos
            schedules = db.schedules
            found = schedules.find_one({'name': self.schedule['name']})
            if found is None:
                schedules.insert(self.schedule)
