# System Identification

During an idle period (like nighttime), we want to perturb the building in order to build up statistical estimates for:
- energy usage for each state of a device
- thermal coupling between rooms/zones
- etc


# Energy Usage per State

## RTU

Have a thermostat independently call for fan, heat and cooling (making sure that all other thermostats are idle).
Recover the raw timeseries for the thermostat state stream to find these transitions.
Define a 30 second window around each transition (15 seconds on either side) and pull the corresponding window from the meter for the RTU (which might be the full building meter).
Look at the largest jump/drop in energy usage (corresponding to activating the state and deactivating the state) in that window, and assign that value to the energy cost of that state.


Requires:
- Thermostat
- Full building power

Brick queries:

- **Thermostat State Transitions**: a thermostat has a `controls` relationship with an RTU, which has 1 or more `feeds` relationships with an HVAC zone. Thermostat control state is called `Thermostat_Status` in Brick, so we retrieve that attribute of a thermostat as well.

  ```sparql
  SELECT ?thermostat ?zone ?state_uuid WHERE {
    ?thermostat rdf:type/rdfs:subClassOf* brick:Thermostat .
    ?zone rdf:type brick:HVAC_Zone .
    ?state rdf:type brick:Thermostat_Status .

    ?thermostat bf:controls/bf:feeds+ ?zone .
    ?thermostat bf:hasPoint ?state .
    ?state bf:uuid ?state_uuid .
  };
  ```

- **Thermostat API**: we want to control the thermostats, so we get the BOSSWAVE URI for each thermostat using a Brick query, using an approach similar to that above:
    ```sparql
  SELECT ?thermostat ?zone ?uri WHERE {
    ?thermostat rdf:type/rdfs:subClassOf* brick:Thermostat .
    ?zone rdf:type brick:HVAC_Zone .

    ?thermostat bf:controls/bf:feeds+ ?zone .
    ?thermostat bf:uri ?uri .
  };
    ```

- **RTU Meters**: We want to remain agnostic to whether or not there is a dedicated meter for the RTU, so we use the following query:
    ```sparql
    SELECT ?rtu ?zone ?meter_uuid WHERE {
        ?rtu rdf:type/rdfs:subClassOf* brick:RTU .
        ?zone rdf:type brick:HVAC_Zone .
        ?meter rdf:type/rdfs:subClassOf* brick:Electric_Meter .

        ?rtu bf:feeds+ ?zone .
        ?rtu bf:hasPoint ?meter .
        ?meter bf:uuid ?meter_uuid .
    };
    ```
