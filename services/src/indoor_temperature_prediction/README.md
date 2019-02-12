# Indoor Temperature Predictions

Forcasts indoor temperatures of HVAC zone.
 
Predictions are based on given features which are assumed to be constant throughout 
a set forecasting range (forecasting_range).  

Using Python 3.6.


### Features

• Current indoor temperature of HVAC zone (t_in)

• Thermal Action to take throughout forecasting range (action)

• Current outdoor temperature  (t_out)

• Current occupancy (occ)

• Current temperature in all other zones in building (temperature_zone_{zone name})

• The indoor temperature measured forecasting_range time before current temperature (t_last)

• Time since the current action has been active in HVAC zone (if not known set to -1) (action_duration)

• Action which was active right before the current action became active (action_last)


## Getting Started


### Prerequisites

See req.txt file. 

### Testing

Tests can be found in the test directory.

## Authors

* **Daniel Lengyel** - *Initial work* - [daniellengyel](https://github.com/daniellengyel)
