# Zone Controller Example

Before reading this, please read the following sMAP wiki pages:

* [Schedules](https://github.com/SoftwareDefinedBuildings/smap/wiki/Scheduler-Service)
* [Zone Controllers](https://github.com/SoftwareDefinedBuildings/smap/wiki/Scheduler-Service)

We consider the following small, 3-room, 2-zone building:

```
<---------------Zone 1-----------------><-----Zone 2----->
+--------------------------------------------------------+
|              |                        |                |
|   *sensor    |    *sensor             |   *sensor      |
|              |                        |                |
|              |                        |                |
|              |                        |                |
| Room 1       |       Room 2           |    Room 3      |
|              |                        |                |
|              |                        |                |
|              |                        |                |
|              |                        |                |
|*thermostat   |                        |*thermostat     |
+--------------------------------------------------------+
```

Each room has a temperature/humidity sensor, but only Rooms 1 and 3 have
thermostats. Each room also has an independent lighting controller.

We have a master schedule and a zone controller each for Zone 1 and Zone 2. We
will have Zone 2 follow the master schedule with a simple trim of 5 degrees F,
and Zone 1 will follow the master schedule, but trim by the difference between
the average sensor temperature and the thermostat's reported temperature.
