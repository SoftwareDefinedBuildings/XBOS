# Structure

What is the structure of OpenBAS as we display the metadata?

First off, there are 4 hierarchies: HVAC, lighting, general and spatial (building). Each of these hierarchies should be represented on the
dashboard page, and you should be able to delve into each of them to "drill down".

## HVAC

For each of the HVAC Zones in a building, render the "thermostat".

The "thermostat" is list of 
* cooling setpoints: `Metadata/Point/Type = Setpoint, Metadata/Point/Setpoint = Cooling`
* heating setpoints: `Metadata/Point/Type = Setpoint, Metadata/Point/Setpoint = Heating`
* temperature sensors: `Metadata/Point/Type = Sensor, Metadata/Point/Sensor = Temperature`

and these should be organized by room w/n the HVAC zone.

Dashboard: `select distinct Metadata/HVACZone`

For each found zone, `select distinct Metadata/Location/Room`

For each room, we want to render heat,cool setpoints, temp and humidity, etc, along with any actuatable points.
How are these grouped? We should try to group these by device w/n each room.

So a room runs, 'select distinct Metadata/DeviceID where Metadata/Location/Room = '410 soda' and Metadata/HVACZone = '410 soda'

for each returned device id, it will render a Device component. That device component should be told what to display in
terms of the metadata tags.

## Lighting

For each of the lighting zones, find all the rooms inside.
For each room, find all lighting groups
For each lighting group, render lighting state


Okay, now I have HVAC and Lighting down. What is the next step?

Todos:
* panel for general control
    * should be fairly straightforward extension of hvac/lighting columns
* scheduler -- display AND implementation
    * in a perfect world...
    * have a scheduler interface very similar to what tyler had before BUT...
    * still have hardcoded names, but make them more explicit.
    * think about to schedule diff devices and setpoints. is there a drop down menu for each
      timeseries that tells which schedule to subscribe to?
    * currently a device needs to enable scheduling. Need to write up a "guide" on what components
      are needed in a driver in order to have a device be fully complicit. How do you do scheduling?
      This list of common features should be in the "new smap driver" framework
    * make the current scheduler a metadata entry, that way it is now changable via a metadata query
* building view
    * this hsould query the building profile. How do we do the building profile?
    * building profile should be a simple database, separate from sMAP. 
    * lets experiment with sqlite3 and a relational model
    * what goes in this model? data about building, floors, list of rooms, equipment, etc

## Scheduler

scheduler will be a smap service that reads the schedule configuration from the building profile and will
publish that schedule to the archiver, where schedulees can subscribe to it.

The scheduler will publish on the path "/schedules/{schedulename}/{schedule point name}".

`schedulename` is a broad name for the whole schedule, e.g. "workday", "save the air day" or "weekend"

`schedule point name` is an enumerated value of what schedule value this is meant for, e.g. Brightness, Heating Setpoint, etc.
TODO: come up with a solid list of these for the ontology

Each timeseries for a schedule should have the following metadata:

Metadata/Schedule/Name = schedulename
Metadata/Schedule/Target = schedule point name

This is putting the path into the metadata, but this is ok bc we do not want to parse the path

the value of the schedule path timeseries is obviously the scheduled value.
Values are pushed ONCE at epoch change.  The "latest value" can be done with
`select data before now where...`.

Those subscribed to a schedule should pay attention to the
Properties/UnitofMeasure and conduct an appropriate conversion.

Need a way for a point to be subscribed to multiple schedules.

```
{
    "master_schedule": {
        "fri": "weekday",
        "mon": "weekday",
        "sat": "weekend",
        "sun": "weekend",
        "thu": "weekday",
        "tue": "weekday",
        "wed": "weekday"
    },
    "schedules": [
        {
            "color": "#EDF1FA",
            "name": "weekday",
            "periods": [
                {
                    "name": "morning",
                    "points": [
                        {
                            "path": "temp_heat",
                            "value": 72
                        },
                        {
                            "path": "temp_cool",
                            "value": 83
                        }
                    ],
                    "start": "7:30"
                },
                {
                    "name": "afternoon",
                    "points": [
                        {
                            "path": "temp_heat",
                            "value": 70
                        },
```
