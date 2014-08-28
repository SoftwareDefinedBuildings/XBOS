Metadata
========

Here, we define a structure for metadata for components of a building as described by sMAP.

## Root-level Metadata

This metadata is specified at `[/]` in the sMAP configuration. As such, this metadata
applies to everything in the configuration file.


Example:
```
[/]
uuid = 06d634a6-1c03-11e4-965d-6003089ed1d0
Metadata/SourceName = Demo Driver
Metadata/Building = Soda Hall
Metadata/Site = 0273d18f-1c03-11e4-a490-6003089ed1d0
Metadata/configured = True
```

#### `Metadata/SourceName`

This is the human-readable name for this configuration file. No specific semantic meaning, but this
is a handy way to refer to the sources contained in this file when you query the archiver.

#### `Metadata/Building`

The name of the building where this is installed. This should be unique to the installation, just as
`Metadata/Site` below.

#### `Metadata/Site`

A UUID that uniquely identifies this installation. All configuration files for all sources for this
installation should have the same `Metadata/Site` at the top level of their configuration.

#### `Metadata/configured`

This is an optional key. If `Metadata/configured = True`, then OpenBAS will assume that the Metadata
specified in all sources in this file is complete, and will not have to be automapped. Typically, this
is false (or unspecified, meaning false) for discovered sources

## Collection-level Metadata

More specific than the global metadata specified by the root collection, collection-level metadata
adds more structure to the hierarchy of metadata in the installation. There are 3 collections that are
expected:

* `/buildinglighting/` -- for lighting-related sources
* `/buildinghvac/` -- for HVAC-related sources
* `/monitoring/` -- for monitoring sources

When defining sources, it is best to stick to this nomenclature, but it is imperative to correct
metadata, described below

#### `Metadata/System`
This describes what function the source performs in the building.

There are 3 valid systems:

* `HVAC`
* `Lighting`
* `Monitoring`

All sources running in a building should belong to one of these systems.

#### `Metadata/Role`

This indicates what this source does within the context of its system. Examples are:

* `Building Lighting`
* `Task Lighting`
* `Building HVAC`
* `Monitoring`

#### `Metadata/Floor`

Which floor the collection is on. This is simply a number. No `4th` or `first floor`. This may also be
device-level metadata.

#### `Metadata/Name`

Human-readable name for this collection

## Device-level Metadata

Device-level metadata is often for a single sMAP driver instantiation, that is,
a single actuatable light or thermostat.

#### `Metadata/Group`
For `Lighting` system devices, a lighting group is the smallest actuatable unit of light. If you have a single
binary switch for a bank of lights, that bank of lights is a 'group'. If we have a driver that controls a single
desk lamp, then that desk lamp is a lighting group.

#### `Metadata/LightingZone`
A lighting zone is defined as the group of lights in a contiguous physical space. Generally, Lighting zones 
are room names, or are based on room names, e.g. '410 Soda' or '420 Soda West'.

#### `Metadata/HVACZone`

Definition here...

## Timeseries-level Metadata

#### `Metadata/Type`

These should be defined for each timeseries within the driver:

* `SP`: setpoint -- does not actually change anything, but serves to direct the device
* `Command`: changes some aspect of the device, e.g. 'on' to 'off'
* `Reading`: reads an aspect or state of the device, e.g. "what is my light's brightness level?"
* `Sensor`: reports an aspect of the physical world
