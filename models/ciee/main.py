TEST_DATE = "2018-01-11 00:00:00 PST"
import pandas as pd

from thermal_model import get_model_per_zone, test_schedule, execute_schedule
print "##################################"
print "####     THERMAL  MODEL      #####"
print "##################################"

models = get_model_per_zone(TEST_DATE) # don't use data after this argument
allactions = None
for zone, model in models.items():
    print "   #####################################################"
    print "   Temperature predictions for", zone
    temps, actions = execute_schedule(TEST_DATE, test_schedule, model, 70) # 70 is starting temperature
    def action_to_energy(x):
        if x == 1:
            return 0.1
        elif x == 2:
            return 5.0
        return 0.0
    actions = pd.Series(actions)
    actions = actions.apply(action_to_energy)
    if allactions is None:
        allactions = actions
    else:
        allactions += actions
    print temps


# weather model
from weather_model import predict_day as predict_weather_day
print "##################################"
print "####        WEATHER          #####"
print "##################################"
print predict_weather_day(TEST_DATE)

# base consumption
from base_consumption import predict_day as predict_consumption_day
print "##################################"
print "####   ENERGY CONSUMPTION    #####"
print "##################################"
base = predict_consumption_day(TEST_DATE)
l = min(len(base), len(allactions))
base = base[:l]
allactions = allactions[:l]
allactions.index = base.index
print 'base + hvac energy'
print base + allactions
