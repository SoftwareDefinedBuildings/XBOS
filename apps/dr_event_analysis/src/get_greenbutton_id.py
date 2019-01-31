import dataclient
m = dataclient.MDALClient("corbusier.cs.berkeley.edu:8088")

def get_greenbutton_id(sitename, time_start, time_stop):
    request = {
        "Variables": {
            "id": {
                "Definition": """SELECT ?gbm ?uuid FROM %s WHERE {
                    ?gbm rdf:type brick:Green_Button_Meter .
                    ?gbm bf:uuid ?uuid
                }; """ % sitename,
            }
        }
    }
    request['Composition'] = ['id']
    request['Aggregation'] = {'id': ['MAX']}
    request['Time'] = {
        'Start': time_start,
        'End': time_stop,
        "Window": '24hr',
        "Aligned": True
    }
    resp = m.query(request)
    return resp.uuids

# print(get_greenbutton_id('ciee', "2018-01-01T10:00:00-07:00", "2018-08-12T10:00:00-07:00"))