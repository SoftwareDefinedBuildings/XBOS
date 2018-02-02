# CIEE Models

You'll need to install (and probably upgrade) the `xbos` module:
`sudo pip2 install --upgrade xbos`

You run this all by running `python main.py`, which calls the other models.


## Thermal Model

Basic linear model based on inside temperature, outside temperature, and HVAC state from some setpoint schedule.

## Weather Model

Similarity-based approach

## Consumption Model

Similarity-based approach, with HVAC energy subtracted. Predicts the base (non-HVAC) load.

I've commented out subtacting the lighting energy for now until I have a schedule for the lights and a model
for their energy consumption (will just be a basic stats model)

## All Together

`main.py` executes the thermal model to get the actions for a thermostat for a basic night/day schedule,
and then rolls those actions forward to get the HVAC energy consumption.

