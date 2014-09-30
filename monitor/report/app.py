from flask import Flask, render_template, url_for, jsonify
import json

data = json.load(open('report.json'))
app = Flask(__name__)

@app.route("/")
def report():
    total_demand = data['demand']['Total Demand']
    reportdata = {k:v for k,v in data['demand'].iteritems() if k not in ["Demand Data", "Total Demand"]}
    return render_template("index.html", total_demand=total_demand, demand=reportdata)

@app.route("/demanddata")
def demanddata():
    return jsonify({'data': [{'date': k,'value': v} for k,v in data['demand']['Demand Data'].iteritems()]})

if __name__=='__main__':
    app.run(debug=True)
