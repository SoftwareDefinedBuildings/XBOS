package main

var zoneQuery = `SELECT ?zone WHERE {
	?zone rdf:type brick:HVAC_Zone .
};`

var tstatTempQuery = `SELECT ?tstat ?temp_uuid ?uri ?zone WHERE {
	?zone rdf:type brick:HVAC_Zone .
	?tstat rdf:type brick:Thermostat .
	?tstat bf:uri ?uri .

	?tstat bf:hasPoint ?ts .
	?ts rdf:type brick:Temperature_Sensor .
	?ts bf:uuid ?temp_uuid .

	?tstat bf:controls/bf:feeds? ?zone .
};`

var tstatHSPQuery = `SELECT ?tstat ?hsp_uuid ?uri ?zone WHERE {
	?zone rdf:type brick:HVAC_Zone .
	?tstat rdf:type brick:Thermostat .
	?tstat bf:uri ?uri .

	?tstat bf:hasPoint ?hsp .
	?hsp rdf:type brick:Supply_Air_Temperature_Heating_Setpoint .
	?hsp bf:uuid ?hsp_uuid .

	?tstat bf:controls/bf:feeds? ?zone .
};`

var tstatCSPQuery = `SELECT ?tstat ?csp_uuid ?uri ?zone WHERE {
	?zone rdf:type brick:HVAC_Zone .
	?tstat rdf:type brick:Thermostat .
	?tstat bf:uri ?uri .

	?tstat bf:hasPoint ?csp .
	?csp rdf:type brick:Supply_Air_Temperature_Cooling_Setpoint .
	?csp bf:uuid ?csp_uuid .

	?tstat bf:controls/bf:feeds? ?zone .
};`

var tstatStateQuery = `SELECT ?tstat ?uri ?zone WHERE {
	?zone rdf:type brick:HVAC_Zone .
	?tstat rdf:type brick:Thermostat .
	?tstat bf:uri ?uri .

	?tstat bf:hasPoint ?stat .
	?stat rdf:type brick:Mode_Status .

	?tstat bf:controls/bf:feeds? ?zone .
};`

var roomSensorZoneQuery = `SELECT ?zone ?room ?uri WHERE {
	?zone rdf:type brick:HVAC_Zone .
	?room rdf:type brick:Room .
	?room bf:isPartOf ?zone .
	?sensor rdf:type/rdfs:subClassOf* brick:Temperature_Sensor .

	?room bf:hasPoint ?sensor .
	?sensor bf:uri ?uri .
};`

var roomList = `SELECT ?zone ?room WHERE {
	?zone rdf:type brick:HVAC_Zone .
	?room rdf:type brick:Room .
	?room bf:isPartOf ?zone .
};`

var roomOccSensorZoneQuery = `SELECT ?zone ?room ?uri WHERE {
	?zone rdf:type brick:HVAC_Zone .
	?room rdf:type brick:Room .
	?room bf:isPartOf ?zone .
	?sensor rdf:type/rdfs:subClassOf* brick:Occupancy_Sensor .

	?room bf:hasPoint ?sensor .
	?sensor bf:uri ?uri .
};`
