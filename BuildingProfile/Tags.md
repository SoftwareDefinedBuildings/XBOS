# General Tags

Here, we describe how tags work, the basic taxonomy, the required expected tags and what they mean. This should be
considered more fundamental than the building profile tags, which will be discussed later.

## Stream Metadata

The primary entity in the system is a stream, which is a sequence of `<timestamp, value>` pairs identified with a UUID and containing
a bag of key-value pairs, which we call the "metadata" of the stream.

Metadata keys are usually drawn from a set of known keys, which promotes interoperability between streams produced by different sources.
Key names are hierarchical, using forward slashes ("/") as the delimiters. Currently, there are 3 top-level "domains" of metadata, some
of which have additional "subdomains":

* `/Properties/`: describes the properties of the stream of tiemseries data
* `/Actuator/`: describes the existence and interface to an actuatable stream
* `/Metadata/`: everything else -- contains subdomains

### Properties

* `UnitofMeasure`: engineering units for the stream. REQUIRED
* `UnitofTime`: the units for the stream's timestamps (`s`, `ms`, `us`, `ns`). Defaults to `ms` (milliseconds)
* `StreamType`: `numeric` or `object`: the data type of the stream. Numeric is any int, uint or float. Object is any JSON-serializable construct.
* `Timezone`: the timezone of the data source 


Notes:
* `UnitofMeasure` needs some form of standardization, else we run into `V` vs `Volt` vs `Volts`, etc. This might be a welcome place
  to include [QUDT](http://www.qudt.org/)
* In practice, `UnitofTime` is often incorrect for a few readings until the producer fixes it (this is often a manual process: "why isn't
  my data showing up on the plotter?"). There should be a good path to "repairing" old data
* `Timezone` is here for historical reasons, but it is not clear what a timezone means when you have a unix timestamp.

### Metadata

Subdomains:
* `Location/`: location of the data stream
* `Point/`: describing what a stream represents
* `Device/`: describing the physical source of a stream
* `Zone/`: 

Terminals;
* `SourceName`
* `Site`

#### Location

* `Building`: the name of the building containing the stream
* `Floor`: the name of the floor containing the stream. This should be a number when possible
* `Room`: the name of the room. This should be a number when possible
* `Exposure`: which cardinal direction is this stream concerned with?

#### Point

* `Type`: this can have one of the four values listed below, and describes the nature of the stream
    * `Sensor`: a transducer that reflects the state of the physical world
    * `State`: reflects the status or configuration; not a transducer
    * `Setpoint`: directs the device to do something
    * `Command`: actually changes some aspect of the device
* `Group`

A stream will have one of the following, which must be the same as the value for `Metadata/Point/Type`.
Each of the following keys has a well-known domain of values
* `Sensor`:
    * Occupancy
    * Humidity
    * Temperature
    * Illumination
    * CO2
* `State`
* `Setpoint`
* `Command`

Notes:
* For the Sensor/State/Setpoint/Command, these can almost certainly be further qualified. For example, a "Temperature" sensor
might want to be qualified by the method of temperature measurement, though I think this is the role of the `Metadata/Device`
subtree

#### Zone

* `Type`: HVAc, lighting?

#### Device

* `ID`: group points toether
* make, model, etc
