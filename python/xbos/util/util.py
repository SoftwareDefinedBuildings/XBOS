import time

def read_self_timeout(self, key, timeout=30):
        start = time.time()
        while self._state.get(key) is None:
            time.sleep(1)
            if time.time() - start > timeout:
                break
        return self._state.get(key)

    
