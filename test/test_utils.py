import grpc
import datetime
import pytz
import sys
import numpy as np
import pandas as pd
from functools import wraps
from enum import Enum

def _log(data):
    assert data, "Nothing to log"
    assert "passed" in data,"Unknown log status"

    class _Logging_ANSI(Enum):
        HEADER = '\033[95m'
        OKBLUE = '\033[94m'
        OKGREEN = '\033[92m'
        WARNING = '\033[93m'
        FAIL = '\033[91m'
        ENDC = '\033[0m'
        BOLD = '\033[1m'
        UNDERLINE = '\033[4m'

    log_color = _Logging_ANSI.OKGREEN.value if data["passed"] else _Logging_ANSI.FAIL.value
    log = ""

    for key in data:
        log += log_color + str(key) + _Logging_ANSI.ENDC.value + ": " + str(data[key]) + ", "

    print(log[:-2])
    print("-------------------------------------------------------")

def all_buildings_and_zones(start=-1, end=-1, logging=True, log_csv="tests.csv", max_interval_days=-1, window="1h", buildings=[], zones=[]):
    def inner(func):
        @wraps(func)
        def loop_buildings(self, *args, **kwargs):
            df = pd.DataFrame(columns=["building","zone", "window", "start", "end", "passed"])
            num_passed = 0

            if start == -1 or end == -1:
                 start_time, end_time = generate_random_time_interval(max_interval_days=max_interval_days)
            else:
                start_time = start
                end_time = end
            total = 0            
            for building in buildings:
                for zone in zones[building]:
                    passed = False
                    try:
                        func(self, building=building, zone=zone, window=window, start=start_time, end=end_time)
                        passed = True
                        num_passed += 1
                    except Exception as e:
                        if e.__class__.__name__ == KeyboardInterrupt:
                            raise
                        else:
                            print(e)
                            pass

                    if logging:
                        data = {"building": building, "zone": zone, "window": window, "start": start_time, "end": end_time, "passed": passed}
                        _log(data)
                    df.loc[total] = [building, zone, window, start_time, end_time, passed]
                    total += 1
            
            print("Num Passed: " + str(num_passed) + " / " + str(total))
            df.to_csv("test_logs/" + log_csv)
        return loop_buildings
    return inner

def random_buildings_and_zones(iterations=1, logging=True, max_interval_days=-1, log_csv="tests.csv", window_unit="h", buildings=[], zones=[]):
    def inner(func):
        @wraps(func)
        def loop_buildings(self, *args, **kwargs):
            df = pd.DataFrame(columns=["building","zone", "window", "start", "end", "passed"])
            total = 0
            num_passed = 0
            for _ in range(iterations):
                window = generate_random_window(window_unit)
                start, end = generate_random_time_interval(max_interval_days=max_interval_days)
                for building in buildings:
                    for zone in zones[building]:
                        passed = False
                        try:                                
                            func(self, building=building, zone=zone, window=window, start=start, end=end)
                            passed = True
                            num_passed += 1
                        except Exception as e:
                            if e.__class__.__name__ == KeyboardInterrupt:
                                raise
                            else:
                                print(e)
                                pass

                        if logging:
                            data = {"building": building, "zone": zone, "window": window, "start": start, "end": end, "passed": passed}
                            _log(data)
                        df.loc[total] = [building, zone, window, start, end, passed]
                        total += 1

            print("Num Passed: " + str(num_passed) + " / " + str(total))
            df.to_csv("test_logs/" + log_csv)
        return loop_buildings
    return inner
        
def all_buildings(start=-1, end=-1, logging=True, log_csv="tests.csv", max_interval_days=-1, window="1h", buildings=[], **extraargs):
    def inner(func):
        @wraps(func)
        def loop_buildings(self, *args, **kwargs):
            columns = ["building", "window", "start", "end"] + list(extraargs) + ["passed"]
            df = pd.DataFrame(columns=columns)
            num_passed = 0

            if start == -1 or end == -1:
                 start_time, end_time = generate_random_time_interval(max_interval_days=max_interval_days)
            else:
                start_time = start
                end_time = end
            total = 0            
            for building in buildings:
                passed = False
                try:
                    func(self, building=building, window=window, start=start_time, end=end_time, **extraargs)
                    passed = True
                    num_passed += 1
                except Exception as e:
                    if e.__class__.__name__ == KeyboardInterrupt:
                        raise
                    else:
                        print(e)
                        pass

                if logging:
                    data = {"building": building, "window": window, "start": start_time, "end": end_time, **extraargs, "passed": passed}
                    _log(data)
                df.loc[total] = [building, window, start_time, end_time] + list(extraargs.values()) + [passed]
                total += 1
            
            print("Num Passed: " + str(num_passed) + " / " + str(total))
            df.to_csv("test_logs/" + log_csv)
        return loop_buildings
    return inner

def random_buildings(start=-1, end=-1, iterations=1, logging=True, max_interval_days=-1, log_csv="tests.csv", window_unit="h", buildings=[], **extraargs):
    def inner(func):
        @wraps(func)
        def loop_buildings(self, *args, **kwargs):
            columns = ["building", "window", "start", "end"] + list(extraargs) + ["passed"]
            df = pd.DataFrame(columns=columns)
            total = 0
            num_passed = 0
            for _ in range(iterations):
                window = "1h" #generate_random_window(window_unit)
                #start, end = generate_random_time_interval(max_interval_days=max_interval_days)
                start = datetime.datetime.strptime("09/09/2018 07:00:00", "%d/%m/%Y %H:%M:%S").replace(tzinfo=pytz.utc)
                end =  datetime.datetime.strptime("31/12/2018 23:59:59", "%d/%m/%Y %H:%M:%S").replace(tzinfo=pytz.utc)
                for building in buildings:
                    passed = False
                    try:                                
                        func(self, building=building, window=window, start=start, end=end, **extraargs)
                        passed = True
                        num_passed += 1
                    except Exception as e:
                        if e.__class__.__name__ == KeyboardInterrupt:
                            raise
                        else:
                            print(e)
                            pass

                    if logging:
                        data = {"building": building, "window": window, "start": start, "end": end, **extraargs, "passed": passed}
                        _log(data)
                    df.loc[total] = [building, window, start, end] + list(extraargs.values()) + [passed]
                    total += 1

            print("Num Passed: " + str(num_passed) + " / " + str(total))
            df.to_csv("test_logs/" + log_csv)
        return loop_buildings
    return inner

#TODO fix to generalize more (i.e. outdoor_temperature_historical)
def only_by_building(logging=True, log_csv="tests.csv", buildings=[], **extraargs):
    def inner(func):
        @wraps(func)
        def loop_buildings(self, *args, **kwargs):
            columns = ["building"] + list(extraargs) + ["passed"]
            df = pd.DataFrame(columns=columns)
            num_passed = 0
            total = 0
            for building in buildings:
                passed = False
                try:
                    func(self, building=building, **extraargs)
                    passed = True
                    num_passed += 1
                except Exception as e:
                    if e.__class__.__name__ == KeyboardInterrupt:
                        raise
                    else:
                        print(e)
                        pass

                if logging:
                    data = {"building": building, **extraargs, "passed": passed}
                    _log(data)
                df.loc[total] = [building] + list(extraargs.values()) + [passed]
                total += 1
            
            print("Num Passed: " + str(num_passed) + " / " + str(total))
            df.to_csv("test_logs/" + log_csv)
        return loop_buildings
    return inner

def random_only_by_building(iterations=1, max_interval_days=-1, logging=True, window_unit="h", log_csv="tests.csv", buildings=[], **extraargs):
    def inner(func):
        @wraps(func)
        def loop_buildings(self, *args, **kwargs):
            columns = ["building", "window", "start", "end"] + list(extraargs) + ["passed"]
            df = pd.DataFrame(columns=columns)
            num_passed = 0
            total = 0      
            for _ in range(iterations):
                window = generate_random_window(window_unit)
                start, end = generate_random_time_interval(max_interval_days=max_interval_days)      
                for building in buildings:
                    passed = False
                    try:
                        func(self, building=building, window=window, start=start, end=end, **extraargs)
                        passed = True
                        num_passed += 1
                    except Exception as e:
                        if e.__class__.__name__ == KeyboardInterrupt:
                            raise
                        else:
                            print(e)
                            pass

                    if logging:
                        data = {"building": building, "window": window, "start": start, "end": end, **extraargs, "passed": passed}
                        _log(data)
                    df.loc[total] = [building, window, start, end] + list(extraargs.values()) + [passed]
                    total += 1
            
            print("Num Passed: " + str(num_passed) + " / " + str(total))
            df.to_csv("test_logs/" + log_csv)
        return loop_buildings
    return inner

def only_by_building_and_zone(logging=True, log_csv="tests.csv", buildings=[], zones=[], **extraargs):
    def inner(func):
        @wraps(func)
        def loop_buildings(self, *args, **kwargs):
            columns = ["building", "zone"] + list(extraargs) + ["passed"]
            df = pd.DataFrame(columns=columns)
            num_passed = 0
            total = 0
            for building in buildings:
                for zone in zones[building]:
                    passed = False
                    try:
                        func(self, building=building, zone=zone, **extraargs)
                        passed = True
                        num_passed += 1
                    except Exception as e:
                        if e.__class__.__name__ == KeyboardInterrupt:
                            raise
                        else:
                            print(e)
                            pass

                    if logging:
                        data = {"building": building, "zone": zone, **extraargs, "passed": passed}
                        _log(data)
                    df.loc[total] = [building, zone] + list(extraargs.values()) + [passed]
                    total += 1
            
            print("Num Passed: " + str(num_passed) + " / " + str(total))
            df.to_csv("test_logs/" + log_csv)
        return loop_buildings
    return inner

def window_to_timedelta(window):
    unit = window[-1]
    time = float(window[:-1])

    units = {
        "h": datetime.timedelta(hours=time),
        "m": datetime.timedelta(minutes=time),
        "s": datetime.timedelta(seconds=time),
        "d": datetime.timedelta(days=time),
        "w": datetime.timedelta(weeks=time),
        "y": datetime.timedelta(weeks=time*52)
    }

    return units[unit]

def generate_random_time_interval(start=-1, end=-1, max_interval_days=-1):
    """ Generates a time interval between 3 years ago and now """
    if start == -1 or end == -1:
        num_years_ago = np.float32(random_float(0.5, 3)).item()
        end = datetime.datetime.now().replace(tzinfo=pytz.utc)
        start = end - datetime.timedelta(weeks=52 * num_years_ago)
    
    if max_interval_days != -1:
        end = start + datetime.timedelta(days=max_interval_days)

    end = start + datetime.timedelta(minutes=np.uint32(random_int(10, int((end - start).total_seconds() / 60))).item())

    return start, end

def generate_random_window(unit="h", minimum=1):
    units = {
        "h": lambda : random_int(0 + minimum, 24),
        "m": lambda : random_int(0 + minimum, 60),
        "s": lambda : random_int(30 + minimum, 3600),
        "d": lambda : random_int(0 + minimum, 30),
        "w": lambda : random_int(0 + minimum, 20),
        "y": lambda : random_int(0 + minimum, 3)
    }

    return str(units[unit]()) + unit

def random_float(minimum, maximum):
    """ Minimum and maximum are inclusive """
    return np.random.uniform(minimum, maximum)

def random_int(minimum, maximum):
    """ Minimum and maximum are inclusive """
    return np.random.randint(low=minimum, high=maximum + 1, size=1)[0]