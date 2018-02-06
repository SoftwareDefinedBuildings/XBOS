import json
from datetime import datetime
from clipper_admin import ClipperConnection, DockerContainerManager
clipper_conn = ClipperConnection(DockerContainerManager())
from thermal_model import get_model_per_zone, normal_schedule, dr_schedule, execute_schedule

try:
    clipper_conn.start_clipper()
    default_output = json.dumps([-1]*24)
    clipper_conn.register_application(name="ciee_thermal", input_type="string", default_output=default_output, slo_micros=1000000000)
    print 'apps', clipper_conn.get_all_apps()
    models = get_model_per_zone("2018-01-30 00:00:00 PST")
    # model parameters:
    #   zone: string
    #   date: string
    #   schedule: [(hsp, csp), ... x 24 ...]
    def execute_thermal_model(params):
        """
        Accepts list of JSON string as argument
        """
        ret = []
        for param in params:
            args = json.loads(param)
            zone = args['zone']
            date = str(args['date'])
            schedule = args['schedule']
            temps, actions = execute_schedule(date, schedule, models[zone], 65)
            ret.append(temps)
        return ret

    from clipper_admin.deployers import python as python_deployer
    python_deployer.deploy_python_closure(clipper_conn, name='thermal-model-ciee', version=1, input_type='strings', func=execute_thermal_model, base_image="xbospy")
    clipper_conn.link_model_to_app(app_name="ciee_thermal", model_name="thermal-model-ciee")
except:
    clipper_conn.connect()

import time
import requests
time.sleep(10)
inp = json.dumps({
        'zone': 'http://buildsys.org/ontologies/ciee#CentralZone',
        'date': '2018-02-06 00:00:00 UTC',
        'schedule': normal_schedule
    })
print inp

resp = requests.post('http://localhost:1337/ciee_thermal/predict', data=json.dumps({'input': inp}))
print resp, resp.content

time.sleep(1)
#clipper_conn.stop_all()
