import numpy as np
import pandas as pd
import configparser
import matplotlib.pyplot as plt

#from Influx_Dataframe_Client import *
import sys
sys.path.append("..")
from Energy_Analytics import Wrapper


# Custom func
def func(X, y):
    from sklearn.linear_model import LinearRegression
    from sklearn.model_selection import cross_val_score
    model = LinearRegression()
    model.fit(X, y)
    return model.predict(X)

# Main
main_obj = Wrapper()

imported_data = main_obj.import_data(folder_name='../data/', head_row=[5,5,0])

cleaned_data = main_obj.clean_data(imported_data, high_bound=9998,
                                rename_col=['OAT','RelHum_Avg', 'CHW_Elec', 'Elec', 'Gas', 'HW_Heat'],
                                drop_col='Elec')

preprocessed_data = main_obj.preprocess_data(cleaned_data, week=True, tod=True)

main_obj.model(preprocessed_data, dep_col='HW_Heat', alphas=np.logspace(-4,1,5), figsize=(18,5),
               time_period=["2014-01","2014-12", "2015-01","2015-12", "2016-01","2016-12"],
               cv=5,
               exclude_time_period=['2014-06', '2014-07'],
               custom_model_func=func)

main_obj.write_json()
