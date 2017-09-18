"""
This library contains a set of utility functions for helping populate points related to smart devices

Given the BOSSWAVE URI for a device, it will look up in the archiver for the related timeseries points, using a regex
on the URI and knowledge of the standard xbos interface.

Each method generates a set of triples instantiating the device and adding the requisite edges for URI/UUID pointers
"""

from rdflib import Graph, Namespace, URIRef, Literal
RDF = Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')
RDFS = Namespace('http://www.w3.org/2000/01/rdf-schema#')
BRICK = Namespace('https://brickschema.org/schema/1.0.1/Brick#')
OWL = Namespace('http://www.w3.org/2002/07/owl#')
BF = Namespace('https://brickschema.org/schema/1.0.1/BrickFrame#')

i_xbos_thermostat_points = {
    'temperature': BRICK.Temperature_Sensor,
    'relative_humidity': BRICK.Relative_Humidity_Sensor,
    'heating_setpoint': BRICK.Supply_Air_Temperature_Heating_Setpoint,
    'cooling_setpoint': BRICK.Supply_Air_Temperature_Cooling_Setpoint,
    'override': BRICK.Override_Command,
    'fan': BRICK.Fan_Command,
    'state': BRICK.Thermostat_Status,
    'mode': BRICK.Thermostat_Mode_Command,
}


i_xbos_light_points = {
    'brightness': BRICK.Lighting_System_Luminance_Command,
    'state': BRICK.Lighting_State,
}

i_xbos_plug_points = {
    'state': BRICK.On_Off_Command,
    'power': BRICK.Electric_Meter,
}

class Generator:
    def __init__(self, bricknamespace, archiverclient):
        self.ns = bricknamespace
        self.archiver = archiverclient

    def add_xbos_thermostat(self, node, uri, controls=None):
        rest_of_uri = '/'.join(uri.split("/")[1:])
        namespace = uri.split("/")[0]
        md = self.archiver.query("select name, uuid where namespace = '{0}' and originaluri like '{1}'".format(namespace, rest_of_uri)).get('metadata')
        triples = []
        triples.append((node, RDF.type, BRICK.Thermostat))
        triples.append((node, BF.uri, Literal(uri)))

        triples.append((BRICK.Thermostat_Status, RDFS.subClassOf, BRICK.Status))
        triples.append((BRICK.Thermostat_Status, RDF.type, OWL.Class))
        triples.append((BRICK.Thermostat_Mode_Command, RDFS.subClassOf, BRICK.Command))
        triples.append((BRICK.Thermostat_Mode_Command, RDF.type, OWL.Class))

        if controls is not None:
            triples.append((node, BF.controls, controls))
        for doc in md:
            if doc['name'] in i_xbos_thermostat_points.keys():
                pointname = self.ns[node.split('#')[-1]+"_"+doc['name']]
                triples.append((pointname, RDF.type, i_xbos_thermostat_points[doc['name']]))
                triples.append((node, BF.hasPoint, pointname))
                triples.append((pointname, BF.uuid, Literal(doc['uuid'])))
        print triples
        return triples

    def add_xbos_light(self, node, uri, controls=None):
        rest_of_uri = '/'.join(uri.split("/")[1:])
        namespace = uri.split("/")[0]
        md = self.archiver.query("select name, uuid where namespace = '{0}' and originaluri like '{1}'".format(namespace, rest_of_uri)).get('metadata')
        print md
        triples = []
        triples.append((node, RDF.type, BRICK.Lighting_System))
        triples.append((node, BF.uri, Literal(uri)))
        if controls is not None:
            triples.append((node, BF.controls, controls))
        for doc in md:
            if doc['name'] in i_xbos_light_points.keys():
                pointname = self.ns[node.split('#')[-1]+"_"+doc['name']]
                triples.append((pointname, RDF.type, i_xbos_light_points[doc['name']]))
                triples.append((node, BF.hasPoint, pointname))
                triples.append((pointname, BF.uuid, Literal(doc['uuid'])))
        print triples
        return triples

    def add_xbos_plug(self, node, uri):
        rest_of_uri = '/'.join(uri.split("/")[1:])
        namespace = uri.split("/")[0]
        md = self.archiver.query("select name, uuid where namespace = '{0}' and originaluri like '{1}'".format(namespace, rest_of_uri)).get('metadata')
        triples = []
        triples.append((BRICK.PlugStrip, RDFS.subClassOf, BRICK.Equipment))
        triples.append((BRICK.PlugStrip, RDF.type, OWL.Class))
        triples.append((node, RDF.type, BRICK.PlugStrip))
        triples.append((node, BF.uri, Literal(uri)))
        for doc in md:
            if doc['name'] in i_xbos_plug_points.keys():
                pointname = self.ns[node.split('#')[-1]+"_"+doc['name']]
                triples.append((pointname, RDF.type, i_xbos_plug_points[doc['name']]))
                triples.append((node, BF.hasPoint, pointname))
                triples.append((pointname, BF.uuid, Literal(doc['uuid'])))
        print triples
        return triples
