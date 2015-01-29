# OpenBAS v2.0

The primary motivation for a rewrite of the OpenBAS front-end is to incorporate
the lessons learned in implementing OpenBAS v1 on top of Meteor, Mongo, and the
original sMAP archiver.

## Application-sMAP Data Model

### Meteor Data Model

Meteor's MongoDB-centric pipeline for reactive applications made things more
complicated than they needed to be. MongoDB was only incorporated into OpenBAS
because Meteor required it in order to do reactive updates to the DOM. The
Meteor server mainly served as a manual pub/sub broker between the sMAP
archiver's HTTP API and MongoDB. This required a number of transformations of
the data as it was sliced, keys were reassigned and portions of data were
placed into multiple MongoDB collections in order to make all of the Meteor
components happy with valid data.

Meteor (at least at the time of writing of OpenBAS, though I don't imagine it
has changed much in this aspect since then) did not have a clear and idiomatic
way of defining modular, nestable, reusable components. The namespaces of each
of the components remained discrete, so nested components had to retrieve data
from their parents in hacky ways (global variable, put another record into a
Mongo collection, access infinitely-nested JS prototypes, etc). Dynamically
inserting new components into the DOM often meant lots of callbacks.
Additionally, all dynamic data updates were doen via Mongo, so the data on the
rendered page did not necessarily affect nor represent what was actually in
sMAP until the server-side polling process of sMAP queries ensured consistency.
This also made code difficult to write correctly, as each additional component
or feature required the programmer to know exactly where new data had to be
placed in order for all the components to remain consistent as well as any
side-effects of doing so.as well as any side-effects of doing so.

What's needed in OpenBAS is a distinction between application data and the
building profile. The building profile is the set of timeseries readings and
metadata documents that consist the physical installation that OpenBAS is
representing. Application data is anything that exists above that. This
distinction was *possible* with the original Meteor implementation of OpenBAS,
but the execution left it too easy to be sloppy.

### ReactJS + WebSockets

ReactJS is a JS library for building user interfaces. It concerns itself
entirely with aspects of the UI, and does not make any assumptions about the
rest of the stack below it. This gives us much more freedom in choosing the
mechanisms for real-time data delivery to the client and allows us to build the
OpenBAS frontend directly over the sMAP archiver while still having a separate
application-specific server program.

Giles, the new sMAP archiver, provides flexibility in the interface for
interaction, meaning we can use a technology such as WebSockets to provide
streams of data to individual components, and have that data trickle down into
the nested components as necessary.

## Device Representation

One of the big hacks that happened in OpenBAS v1 was the shimming tactic of
attempting to represent a collection of timeseries as a cohesive body. sMAP is
timeseries oriented, so UUIDs are handed out for individual timeseries. The
concept of a physical device having multiple timeseries must be captured by
arbitrary Metadata key/values, rather than an attribute intrinsic to the
representation of a timeseries.

### Example

One of the visual components of OpenBAS v1 was a high-level view of the HVAC zones
and the status of the thermostat(s) therein. This was accomplished by several queries
to the sMAP backend.

`select distinct Metadata/HVACZone where Metadata/Site = {uuid here}` retrieves
a list of string values corresponding to the HVAC zone label for our
installation (`Metadata/Site`).

For each HVAC zone label, we needed to get information on the thermostats:
`select * where Metadata/HVACZone = {hvac zone label} and Metadata/Device =
'Thermostat'` will return a list of JSON objects for each of the timeseries
that fit the criteria:

```json
[
  {
    "Metadata": {
      "Building": "Soda Hall",
      "Device": "Thermostat",
      "Driver": "smap.drivers.thermostats.virtualthermostat",
      "Floor": "4",
      "HVACZone": "410 Soda E",
      "Model": "Virtual Thermostat",
      "Name": "4th Floor HVAC",
      "Role": "Building HVAC",
      "Room": "410 Soda",
      "Site": "0273d18f-1c03-11e4-a490-6003089ed1d0",
      "SourceName": "Demo Driver",
      "System": "HVAC",
      "configured": "True"
    },
    "Path": "/buildinghvac/thermostat1/hvac_state",
    "Properties": {
      "ReadingType": "long",
      "Timezone": "America/Los_Angeles",
      "UnitofMeasure": "Mode",
      "UnitofTime": "s"
    },
    "uuid": "4aa66a63-925e-5f0a-9410-39063b535527"
  },
  {
    "Metadata": {
      "Building": "Soda Hall",
      "Device": "Thermostat",
      "Driver": "smap.drivers.thermostats.virtualthermostat",
      "Floor": "4",
      "HVACZone": "410 Soda E",
      "Model": "Virtual Thermostat",
      "Name": "4th Floor HVAC",
      "Role": "Building HVAC",
      "Room": "410 Soda",
      "Sensor": "Humidity",
      "Site": "0273d18f-1c03-11e4-a490-6003089ed1d0",
      "SourceName": "Demo Driver",
      "System": "HVAC",
      "Type": "Sensor",
      "configured": "True"
    },
    "Path": "/buildinghvac/thermostat1/humidity",
    "Properties": {
      "ReadingType": "long",
      "Timezone": "America/Los_Angeles",
      "UnitofMeasure": "%RH",
      "UnitofTime": "s"
    },
    "uuid": "ebf1a17a-2edd-5604-a1c1-7ab3bab0ee65"
  },
  etc...
```

The issue now arises: for rendering a component in the DOM, it is relevant to
know which JSON object corresponds to which aspect of the device. If I wish to
label the heating setpoint `temp_heat`, then I have to search through the
returned array for the correct JSON object. Having an object representation
that maps the key `temp_heat` to the correct JSON object would simplify
development. Placing the necessary transformation in an intelligent place would
reduce the number of O(n) searches done when rendering the DOM.

The other issue is one of ownership and grouping. If multiple thermostats were
returned for my above query, then they would all be returned in the same flat
list of JSON objects. OpenBAS v1 did some string slicing and a groupBy
operation in order to group together timeseries with the same `Path` prefix,
but this does not scale to other devices where the sMAP driver is really a
gateway, and the relationships and groupings between timeseries is less
intuitive or more subtle. What is needed is a device UUID that simplifies this
grouping such that it may be specified by the driver source instead of being
gleaned in postprocessing (which may lead to mistakes).
