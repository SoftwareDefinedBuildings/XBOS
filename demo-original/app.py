from flask import Flask, render_template, jsonify, url_for, request
import json
import traceback
import requests
import time
from smap.client import SmapClient
from bosswave import BossWave
from twisted.internet import reactor, task
fanstate = 0

tempsensors = [0]*4
currenttick = -1

c_url = 'http://128.32.37.43:8080/data'
c = SmapClient('http://128.32.37.43:8080')
print c.contents()

other_url = 'http://128.32.37.43:8081/data'
otherclient = SmapClient('http://128.32.37.43:8081')
print otherclient.contents()

acts = {'spaceheater': c_url+'/Raritan/outlet2/state_act',
        'tasklight': c_url+'/TCPLighting/216544666156982628/state_act',
        'buildinglight': c_url+'/hue/workbench/state/on_act',
        'heatspt': c_url+'/imt550c0/temp_heat_act',
        'coolspt': c_url+'/imt550c0/temp_cool_act',
        }

objects = {
'spaceheater': {
    'status': 'http://128.32.37.43:8080/data/Raritan/outlet2/state',
    'actuate': 'http://128.32.37.43:8080/data/Raritan/outlet2/state_act',
    'cssid': 'spaceheater'},
'rtuheat': {
    'status': 'http://128.32.37.43:8080/data/Raritan/outlet3/state',
    'actuate': 'http://128.32.37.43:8080/data/Raritan/outlet3/state_act',
    'cssid': 'rtuheat'},
'tasklight': {
    'status': 'http://128.32.37.43:8080/data/TCPLighting/216544666156982628/state',
    'actuate': 'http://128.32.37.43:8080/data/TCPLighting/216544666156982628/state_act',
    'cssid': 'tasklight'},
'buildinglight': {
    'status': 'http://128.32.37.43:8080/data/hue/workbench/state/on',
    'actuate': 'http://128.32.37.43:8080/data/hue/workbench/state/on_act',
    'cssid': 'buildinglight'},
'buildinglighthue': {
    'status': 'http://128.32.37.43:8080/data/hue/workbench/state/hue',
    'actuate': 'http://128.32.37.43:8080/data/hue/workbench/state/hue_act',
    'cssid': 'buildinghue'},
'buildinglightbri': {
    'status': 'http://128.32.37.43:8080/data/hue/workbench/state/bri',
    'actuate': 'http://128.32.37.43:8080/data/hue/workbench/state/bri_act',
    'cssid': 'buildingbri'},
'heatspt': {
    'status': 'http://128.32.37.43:8080/data/imt550c0/temp_heat',
    'actuate': 'http://128.32.37.43:8080/data/imt550c0/temp_heat_act',
    'cssid': 'heatspt'},
'coolspt': {
    'status': 'http://128.32.37.43:8080/data/imt550c0/temp_cool',
    'actuate': 'http://128.32.37.43:8080/data/imt550c0/temp_cool_act',
    'cssid': 'coolspt'},
'thermostat': {
    'status': 'http://128.32.37.43:8080/data/imt550c0/temp',
    'cssid': 'temp'},
'rtucool': {
    'status': 'http://128.32.37.43:8081/data/sensors/fan',
    'actuate' : 'http://128.32.37.43:8081/data/sensors/fan_act',
    'cssid': 'rtucool'},
'room1temp': {
    'status': 'http://128.32.37.43:8081/data/sensors/temp1',
    'cssid': 'room1temp'},
'room2temp': {
    'status': 'http://128.32.37.43:8081/data/sensors/temp2',
    'cssid': 'room2temp'},
'room1rh': {
    'status': 'http://128.32.37.43:8081/data/sensors/rh1',
    'cssid': 'room1rh'},
'room2rh': {
    'status': 'http://128.32.37.43:8081/data/sensors/rh2',
    'cssid': 'room2rh'},
}

def actuate_fan(state):
    try:
        if int(state) == 1:
            otherclient.set_state('/sensors/fan_act',1)
        else:
            otherclient.set_state('/sensors/fan_act',0)
    except Exception as e:
        print e

def c_to_f(temp):
    return temp * (9./5) + 32

def runschedule(f):
    global currenttick
    current_states = map(lambda x: json.loads(requests.get(x[:-4]).content)['Readings'][0][1], acts.itervalues())
    for i in range(0,6):
        print i
        currenttick = i
        todo = [(acts[k[:-1]],v) for k,v in f.iteritems() if k.endswith(str(i))]
        for url, val in todo:
            if url:
                print requests.put(url+'?state='+val)
        time.sleep(10)
    currenttick = -1
    for url, val in zip(acts.values(), current_states):
        print requests.put(url+'?state='+str(val))

app = Flask(__name__)

@app.route("/")
def index():
    return render_template('index.html')

@app.route('/schedule', methods=['GET','POST'])
def handleform():
    reactor.callInThread(runschedule, request.form)
    return jsonify({'ok': 0})

@app.route('/scheduletick', methods=['GET'])
def gettick():
    global currenttick
    return jsonify({'tick': currenttick})

@app.route('/smap', methods=['GET'])
def getsmap():
    path = request.args.get('smappath')+'/'
    actpath = request.args.get('smappath')+'_act/'
    state = c.get_state(path)[1]
    act_state = request.args.get('state',None)
    toggle = request.args.get('toggle',None)
    try:
        if toggle:
            if int(state) == 1:
                c.set_state(actpath,0)
            else:
                c.set_state(actpath,1)
        elif act_state:
            resp = requests.get('http://128.32.37.43:8080/data'+path)
            if json.loads(resp.content)['Readings'][0][1] == int(act_state):
                print 'already okay',act_state,actpath
            else:
                print 'http://128.32.37.43:8080/data'+actpath[:-1]+'?state='+act_state
                print requests.put('http://128.32.37.43:8080/data'+actpath+'?state='+act_state)
            #c.set_state(actpath, int(act_state))
    except Exception as e:
        print e#, traceback.format_exc()
    resp = jsonify({'Reading': c.get_state(path)[1]})
    resp.headers['Access-Control-Allow-Origin']='*'
    return resp

@app.route('/fan', methods=['GET'])
def fan():
    state = -1
    try:
        state = int(request.args.get('state'))
    except:
        pass
    global fanstate
    if (state == 0 or state == 1):
        actuate_fan(state)
        fanstate = state
        return jsonify({'Readings': [[1, state]]})

    if fanstate == 0:
        actuate_fan(1)
        fanstate = 1
        return jsonify({'Readings': [[1, 1]]})
    else:
        actuate_fan(0)
        fanstate = 0
        return jsonify({'Readings': [[0, 0]]})

@app.route('/objectmap')
def getobjectmap():
    return json.dumps(objects)

if __name__ == '__main__':
    from twisted.internet import reactor
    from threading import Thread

    Thread(target=reactor.run, args=(False,)).start()
    app.run(host='0.0.0.0',port=5000,debug=True)

