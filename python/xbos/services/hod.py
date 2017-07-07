import requests
import json

class HodClientHTTP(object):
    def __init__(self, url="http://localhost:47808"):
        self.url = url
    def do_query(self, query, values_only=True):
        url = self.url+'/api/query'
        resp = requests.post(url, data=query)
        if not resp.ok:
            raise Exception("Query to {0} failed ({1})".format(self.url, resp.reason))
        d = resp.json()
        count = d['Count']
        elapsed = d['Elapsed']
        rows = d['Rows']
        if values_only:
            rows = [{k: v['Value'] for k,v in r.items()} for r in rows]
        return rows
