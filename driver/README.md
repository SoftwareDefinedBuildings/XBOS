# XBOS Driver

This is a Go core framework for building XBOS drivers. The goal here is to unify many of the design points and features which are only idiom or only dreams.

Features will include:
- state management: functions to be invoked when the driver enters different states
- intermittent connectivity: local buffering backed by disk with replay functionality
- integrated metadata management: implement metadata interface
- transport agnostic: plug your own transport in!

## Interface Definitions

In the YAML file for the interface, we need a definition of the fields
```yaml
Fields:
    - name: temperature
      type: double
      description: Current measured temperature
      units: F
    - name: relative_humidity
      type: double
      description: Current measured relative humidity
      units: %RH
    - name: thermostat_state
      type: uint
      description: Current operating activity of thermostat
      units: TSTAT_STATE_ENUM
    - name: time
      type: uint64
      description: nanoseconds since the Unix epoch
      units: ns
Units:
    TSTAT_STATE_ENUM:
        0: Off
        1: Heating
        2: Cooling
        3: Auto
```

When device interfaces are implemented, they should adhere to these definitions.

## Buffering

Each of the messages we send has a `[]byte` serialization. Messages are published on a URI. We want to give each of these a monotonic sequence number. This sequence number is established and is incremented for each URI

Going to adopt the WAL from bw2bind BUT the key is now HASH (murmur3) of the URI followed by a 4-byte sequence number. This is so we can do prefix range scans on the database.
