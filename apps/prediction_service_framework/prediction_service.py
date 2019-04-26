from xbos import get_client
import threading
from bw2python import ponames
from bw2python.bwtypes import PayloadObject
from dateutil.parser import parse
import time
import msgpack
import config
from util import get_today
import datetime


def run_service(prediction_fxn, namespace, prediction_type, block=False):
    """
    Supported prediction_type:
    - hvac
    - occupancy
    """
    subscribe = '{0}/s.predictions/+/i.{1}/slot/request'.format(namespace, prediction_type)
    if block:
        print 'Blocking is True! This will loop forever and program will not exit until killed'
    else:
        print 'Blocking is False! This will run in background until program exits or is killed'
    print 'Subscribe on', subscribe
    def run():
        c = get_client(config.AGENT, config.ENTITY)
        def cb(msg):
            po = msgpack.unpackb(msg.payload_objects[0].content)
            if not isinstance(po, dict): return
            client_id = msg.uri.split('/')[2]
            start = po.get('predstart')
            start = parse(start) if start else get_today()
            end = po.get('predend')
            end = parse(end) if end else get_today()+datetime.timedelta(days=1)
            resolution = po.get('resolution', '1h')
            result = prediction_fxn(start, end, resolution)
            po = PayloadObject((2,0,0,0), None, msgpack.packb(result))
            publish = '{0}/s.predictions/{1}/i.{2}/signal/response'.format(namespace, client_id, prediction_type)
            print "Respond on", publish
            c.publish(publish, payload_objects=(po,))
        c.subscribe(subscribe, cb)
        while True:
            time.sleep(10)
    t = threading.Thread(target=run)
    t.daemon = True
    t.start()
    while block:
        time.sleep(10)
    return t

if __name__ == '__main__':
    # USAGE:
    import dummy_prediction_hvac
    # use block="True" if you want this to keep your program running. If block="False", this will run in the background
    thread = run_service(dummy_prediction_hvac.my_hvac_prediction_function, 'scratch.ns','hvac', block=True)
