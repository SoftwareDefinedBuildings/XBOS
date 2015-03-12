# OpenBAS: ReactJS + Socket.IO + Websockets

I like this setup


## Setting Up

You will need 

* [bower](http://bower.io/)
* [npm](https://docs.npmjs.com/getting-started/installing-node)

which are both fairly standard JS tools. The individual packages we are using
can be found in `package.json` for server-side packages, and `bower.json` for
client-side packages. To install everything, run

```bash
$ cd openbas_reactjs_socketio
$ bower install
$ npm install
```

The ReactJS JSX files (essentially the source files for the client application)
need to be compiled before they can be used. Until I can think of (or find the
standard way of) distributing the compiled JSX files, I run the JSX compiler
in "watch" mode from the `public` directory:

```bash
$ jsx -w ../react_src/ build/
```

This won't terminate; it will continuously compile your JSX files in `react_src`
and report any syntax errors.

To run the server, run

```bash
$ npm start
```

from the repository's root directory. Right now, every time I change the ReactJS
source files, I have to restart the server. There's probably a way round this, but
I don't know what it is yet.

**Make sure you are running Giles as well.**

## How Does It Work?

### Receiving Data

There are two ways that React views can retrieve data from the archiver:

* execute a one-time query: this is typically done on the
  initialization/creation of a view, and is to be used to get static data. An
  example of this is the one-time query done to get a list of HVAC zones. This
  query will be run every time the component is rendered, so if we click away
  or refresh the page, we get up-to-date data. See `componentDidMount` in the
  `ThermostatList` component.
* continuous query: to be used for changing data, mostly sensor
  readings/setpoints/etc.  This is done through [socket.io](http://socket.io/),
  a realtime pub-sub engine for JavaScript that abstracts away many of the
  annoying details. Upon initialization, the React component "emits" a sMAP
  metadata query describing the desired republish subscription to the `"new
  subscribe"` topic. The query string is used as the socket topic. In the
  server, we subscribe to any new subscription that come on the `"new
  subscribe"` topic.  For each one (making sure to toss duplicates), we create
  a new WebSocket connection to the archiver. Messages received from the
  archiver are then forwarded to clients. The fan-out from server to client is
  handled seemlessly by socket.io.

### Sending Data

It's not yet clear what the best way to handle this is. For sMAP source URIs that
have actuators, the URI will have a JSON object that looks something like this:

```json
{
    "Actuator": {
        "path": "/buildinghvac/thermostat0/temp_heat_act",
        "uuid": "1eacb08b-954a-5f25-a634-500cc3320c4b"
    },
    "Metadata": {
        "Type": "Reading"
    },
    "Properties": {
        "ReadingType": "long",
        "Timezone": "America/Los_Angeles",
        "UnitofMeasure": "F",
        "UnitofTime": "s"
    },
    "Readings": [
        [
            1425595914,
            71
        ]
    ],
    "uuid": "0b7ab090-9756-5fb7-b7d4-038e11aa65c4"
}

```

The `Actuator` key gives us a reference to the URI of the actuator relative to
the current sMAP source. If we then visit that, then we can see the actuator
along with some additional information about it.

```json
{
    "Actuator": {
        "Model": "continuousInteger",
        "States": [
            45,
            95
        ]
    },
    "Metadata": {
        "Type": "SP"
    },
    "Properties": {
        "ReadingType": "long",
        "Timezone": "America/Los_Angeles",
        "UnitofMeasure": "F",
        "UnitofTime": "s"
    },
    "Readings": [
        [
            1425596122000,
            71
        ]
    ],
    "uuid": "1eacb08b-954a-5f25-a634-500cc3320c4b"
}
```

What we don't get from the Actuator description in the parent timeseries is the
port on which the sMAP source is running. Because sMAP processes can operate on
different ports -- and in fact have to unless they are consolidated into a
single process designated by a single config `.ini` file -- we do in fact need
that piece of information.

The problem is that sMAP doesn't provide a good enough abstraction for writing
data to an actuator as well as it does for reading sources.

The best solution we have right now that doesn't involve changing the sMAP
fundamentals is through sMAP's republish mechanism. By default, each actuator
should subscribe to a query that is specifically for itself, e.g.
`Metadata/override = "1eacb08b-954a-5f25-a634-500cc3320c4b"`. The actuator can subscribe
to other sources over that, of course, but this provides a way for individual
actuations to be done.

Because of client fan-out, it makes sense to have the client relay their
actuation requests to the application server, which then interacts directly
with Giles. This can be accomplished in two ways: 1) the app server acts as a
single sMAP driver that changes its metadata depending on which point is being
actuated, or 2) the app server creates a number of streams equal to the number
of actuators, and simply switches which stream to publish on.
