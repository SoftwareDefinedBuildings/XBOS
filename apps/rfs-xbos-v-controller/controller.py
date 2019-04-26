import time
import msgpack
import operator
from bw2python.client import Client
from xbos.services.hod import HodClient
from xbos.devices.thermostat import Thermostat
from xbos.devices.plug import Plug
from xbos.devices.meter import Meter
from xbos.devices.evse import EVSE

_BASEBOARD_HEATER_CONSUMPTION = 1100 #W
_MAX_EVSE_CONSUMPTION = 6600 #W 30A x 220V
_MIN_EVSE_CONSUMPTION = 1320 #W 6A x 220V
_MAX_EVSE_CURRENT = 30 #A
_MAX_POWER_CONSUMPTION = 6000 #W
_CONTROL_FREQUENCY = 60 #seconds

class Controller:
    def __init__(self):
        self.bw_client = Client()
        self.bw_client.setEntityFromEnviron()
        self.bw_client.overrideAutoChainTo(True)
        self.hod_client = HodClient("xbos/hod", self.bw_client)
        self.priority = {
            "fan":1,
            "kettle":2,
            "student_office_tstat":3,
            "microwave":4,
            "sra_office_tstat":5,
            "space_heater":5,
            "fridge":6,
            "evse":7,
            "michaels_office_tstat":8
        }

        meter_q = """
            SELECT ?uri FROM rfs WHERE {
            ?m rdf:type brick:Building_Electric_Meter .
  	         ?m bf:uri ?uri .
             };
        """
        self.building_meter = Meter(self.bw_client,self.hod_client.do_query(meter_q)['Rows'][0]['?uri'])
        self.tstats = {
            "student_office_tstat":Thermostat(self.bw_client,"rfs/devices/s.pelican/Student_Office/i.xbos.thermostat"),
            "sra_office_tstat":Thermostat(self.bw_client,"rfs/devices/s.pelican/SRA_Office/i.xbos.thermostat"),
            "michaels_office_tstat":Thermostat(self.bw_client,"rfs/devices/s.pelican/Michaels_Office/i.xbos.thermostat")
        }

        self.plugloads = {
            "fan":Plug(self.bw_client,"rfs/devices/fan/s.tplink.v0/0/i.xbos.plug"),
            "fridge":Plug(self.bw_client,"rfs/devices/refrigerator/s.tplink.v0/0/i.xbos.plug"),
            "space_heater":Plug(self.bw_client,"rfs/devices/heater/s.tplink.v0/0/i.xbos.plug"),
            "kettle":Plug(self.bw_client,"rfs/devices/boiler/s.tplink.v0/0/i.xbos.plug"),
            "microwave":Plug(self.bw_client,"rfs/devices/microwave/s.tplink.v0/0/i.xbos.plug")
        }
        self.evse = EVSE(self.bw_client,"rfs/devices/s.aerovironment/ParkingLot/i.xbos.evse")
        self.evse.set_current_limit(_MAX_EVSE_CURRENT)


    def control(self,threshold):
        if self.evse.state:
            car_demand = self.evse.current*self.evse.voltage
            allowed_car_threshold = threshold - self.building_meter.power*1000
            if car_demand  < allowed_car_threshold:
                if self.evse.current_limit <_MAX_EVSE_CURRENT:
                    print("current total consumption is less than threshold, increasing car charging limit")
                    if allowed_car_threshold < _MAX_EVSE_CONSUMPTION:
                        print("setting limit to:",(allowed_car_threshold)//_MAX_EVSE_VOLTAGE)
                        self.evse.set_current_limit((allowed_car_threshold)//_MAX_EVSE_VOLTAGE)
                    else:
                        print("setting limit to:",_MAX_EVSE_CURRENT)
                        self.evse.set_current_limit(_MAX_EVSE_CURRENT)
                else:
                    print("current total consumption is less than threshold, evse limit is already at max nothing to do")
                return
        else:
            if self.building_meter.power <= threshold:
                print("current building consumption is less than threshold and evse is off, nothing to do")
                return

        # current consumption is higher than threshold

        # get total power consumption of controllable loads without evse (plugloads and baseboard heaters)
        controllable_loads = 0

        for _,tstat in self.tstats.iteritems():
            controllable_loads += (tstat.state * _BASEBOARD_HEATER_CONSUMPTION)

        for _, plug in self.plugloads.iteritems():
            controllable_loads += plug.power

        print("Building electric meter:",self.building_meter.power*1000)
        print("Total controllable_loads power:",controllable_loads)
        process_load = self.building_meter.power*1000 - controllable_loads
        print("Total process (uncontrollable) loads power:",process_load)

        # if process_load is greater than threshold
        if process_load >= threshold:
            if controllable_loads == 0:
                print("current consumption is greater than threshold, but all controllable_loads are off, nothing to do")
                return
            else:
                print("current consumption is greater than threshold, turning off all controllable loads. nothing else to do")
                for _,tstat in self.tstats.iteritems():
                    tstat.set_mode(0)

                for _, plug in self.plugloads.iteritems():
                    plug.set_state(0.0)

                self.evse.set_state(False)
                return

        # subtract uncontrollable loads from threshold
        ctrl_threshold = threshold - process_load
        print("Controllable threshold:",ctrl_threshold)

        # get and sort controllable_loads
        controllable_loads = [
        {'name':'fan', 'priority' : self.priority.get('fan'), 'capacity' :self.plugloads.get('fan').power ,'state':int(self.plugloads.get('fan').state)},
        {'name':'kettle','priority': self.priority.get('kettle'),'capacity': self.plugloads.get('kettle').power ,'state':int(self.plugloads.get('kettle').state)},
        {'name':'student_office_tstat','priority':self.priority.get('student_office_tstat'),'capacity': _BASEBOARD_HEATER_CONSUMPTION,'state':self.tstats.get('student_office_tstat').state },
        {'name':'microwave','priority':self.priority.get('microwave'),'capacity': self.plugloads.get('microwave').power ,'state':int(self.plugloads.get('microwave').state)},
        {'name':'sra_office_tstat','priority': self.priority.get('sra_office_tstat'),'capacity': _BASEBOARD_HEATER_CONSUMPTION ,'state':self.tstats.get('sra_office_tstat').state},
        {'name':'space_heater','priority': self.priority.get('space_heater'),'capacity': self.plugloads.get('space_heater').power ,'state':int(self.plugloads.get('space_heater').state)},
        {'name':'michaels_office_tstat','priority':self.priority.get('michaels_office_tstat'),'capacity': _BASEBOARD_HEATER_CONSUMPTION ,'state':self.tstats.get('michaels_office_tstat').state},
        {'name':'fridge','priority':self.priority.get('fridge'),'capacity': self.plugloads.get('fridge').power ,'state':int(self.plugloads.get('fridge').state)},
        {'name':'evse','priority':self.priority.get('evse'),'capacity': _MIN_EVSE_CONSUMPTION ,'state':int(self.evse.state)}
        ]
        controllable_loads = sorted(controllable_loads, key=operator.itemgetter('priority', 'capacity'),reverse=True)
        loads_to_keep = []
        # get loads to keep on
        for load in controllable_loads:
            if load['state'] ==1 and load['capacity'] <= ctrl_threshold:
                print load
                loads_to_keep.append(load['name'])
                ctrl_threshold -= load['capacity']
                print("Updated controllable threshold:",ctrl_threshold)
        # turn off other loads
        for load in controllable_loads:
            if load['state'] ==1 and load['name'] not in loads_to_keep:
                if load['name']=='evse':
                    print "turning off evse"
                    self.evse.set_state(False)
                elif load['name'].endswith('_tstat'):
                    print "turning off tstat: "+ load['name']
                    self.tstats.get(load['name']).set_mode(0)
                else:
                    print "turning off plug: "+ load['name']
                    self.plugloads.get(load['name']).set_state(0.0)
        # set current_limit for evse to match threshold
        if ctrl_threshold > 0 and 'evse' in loads_to_keep:
            if _MIN_EVSE_CONSUMPTION + ctrl_threshold < _MAX_EVSE_CONSUMPTION:
                print("setting limit to:",(_MIN_EVSE_CONSUMPTION + ctrl_threshold)//_MAX_EVSE_VOLTAGE)
                self.evse.set_current_limit((_MIN_EVSE_CONSUMPTION + ctrl_threshold)//_MAX_EVSE_VOLTAGE)
            else:
                print("setting limit to:",_MAX_EVSE_CURRENT)
                self.evse.set_current_limit(_MAX_EVSE_CURRENT)

    def report_state(self):
        print("EVSE state: ",self.evse.state)
        print("EVSE current: ",self.evse.current)
        print("EVSE voltage: ",self.evse.voltage)
        print("Building_Electric_Meter: ",self.building_meter.power*1000)
        for _,tstat in self.tstats.iteritems():
            print("Tstat ",tstat._uri," State: ",tstat.state)
            print("Tstat ",tstat._uri," Power: ",tstat.state* _BASEBOARD_HEATER_CONSUMPTION)
        for _, plug in self.plugloads.iteritems():
            print("Plugload ",plug._uri," State: ",plug.state)
            print("Plugload ",plug._uri," Power: ",plug.power)


if __name__ == '__main__':
    c = Controller()
    c.report_state()
    while True:
        c.control(_MAX_POWER_CONSUMPTION)
        c.report_state()
        time.sleep(_CONTROL_FREQUENCY)
