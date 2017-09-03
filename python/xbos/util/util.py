import time

class TimeoutException(Exception):
    pass

def read_self_timeout(self, key, timeout=30):
        start = time.time()
        while self._state.get(key) is None:
            time.sleep(1)
            if time.time() - start > timeout:
                raise TimeoutException("Read of {0} timed out".format(key))
        return self._state.get(key)

def pretty_print_timedelta(td):
    res = ""
    if td.days:
        res += "{0} hours ".format(td.days)
    if td.seconds:
        res += "{0} seconds ".format(td.seconds)
    if td.microseconds:
        res += "{0} ms ".format(td.microseconds / 1000.)
    return res+"ago"
