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

## Two-Way Data Flow

One of the consequences of the original sMAP architectural formulation in which
the archiver was an optional component instead of a central hub is the fact
that there is no well-defined way to push data back to the sMAP sources. sMAP
sources support local actuation, that is, a POST request sent to a special
timeseries endpoint on the driver instance. In OpenBAS, we often have the case
in which a user clicks a button or drags a slider and wants to enact something
on one of the running drivers. OpenBAS v1 made changes to the sMAP driver such
that the actuator descriptions exposed the port they were running on, and then
the client-side JavaScript made POST requests to URLs that were constructed
from the actuator description and the assumption that all drivers were running
on the host machine.

This assumption and the accompanying mechanism for actuation was hacky, but
worked for the single-machine philosophy of OpenBAS v1. Moving forward, we
would like to enable the possibility of having sMAP drivers running on external
devices, invalidating the assumption that all drivers are running on the same
host machine. Additionally, having clients blindly POST to internal ports means
that those internal ports must be public, which should be unnecessary and makes
the whole system less secure. If we position OpenBAS in a home- or
building-area network, then the devices in that home should not be exposed past
the NAT box.

There is already an external connection from the local drivers to the
(potentially) external archiver. Could this be two-way?

## Architectural Proposal

Each deployment will either have or connect to a Giles archiver running with
MongoDB as a metadata store and Quasar as a timeseries database (making sure to
drastically reduce the cache size on Quasar). The deployment will be
identifiable by each of the sMAP sources having the same `Metadata/Site` UUID,
which is how it is currently done.

The OpenBAS server process will serve the requisite HTML/CSS/JS required for
the various sites. We're are no longer making the assumption that OpenBAS
consists solely of the web application -- the server process should facilitate
deploying and running other applications on top of the OpenBAS API. The server
will open a WebSockets connection to Giles and will use that connection as the
mechanism for executing queries. The server process will probably be written
in NodeJS, but this is not necessary. Server process could also use regular HTTP
requests as well.

The client-facing application will be written using the ReactJS view framework,
using socket.io to the server process as the transport for the constant data
flow. This means that the number of websockets connections against Giles will
only scale with the number of deployments against it, not the number of clients
visiting the site (not that Giles needs help with this). Placing logic on the
server also means that we can have actuations/metadata commands be sent from
the client to the server rather than the archiver directly. The server can now
know the API key instead of each of the clients. Having a server process will
also give us a place to store application-specific data.

### Helpful Blog Posts

* http://blog.mgechev.com/2014/09/03/webrtc-peer-to-peer-chat-with-react/
* http://codelinks.net/reactjs-and-d3-build-real-time-components/
* https://github.com/javaguirre/twitter-streaming-api-example
