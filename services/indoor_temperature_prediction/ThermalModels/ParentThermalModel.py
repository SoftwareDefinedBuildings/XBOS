import os, sys
FILE_PATH = os.path.dirname(os.path.abspath(__file__))
xbos_services_path = os.path.dirname(os.path.dirname(os.path.dirname(FILE_PATH)))
sys.path.append(xbos_services_path)

import utils3 as utils
import numpy as np

from abc import ABCMeta, abstractmethod


class ParentThermalModel:
    """A Parent to the thermal model class which implements all the logic to score and predict."""

    __metaclass__ = ABCMeta

    def __init__(self, thermal_precision, interval_thermal):
        # the thermal precision when rounding
        self.thermal_precision = thermal_precision

        # the number of minutes that the thermal models learns to predict for.
        self.interval_thermal = interval_thermal

    @abstractmethod
    def _features(self, X):
        """Returns the features we are using as a matrix.
        :param X: A matrix with column order (Tin, a1, a2, Tout, dt, rest of zone temperatures)
        :return np.matrix. each column corresponding to the features in the order of self._param_order"""
        pass

    @abstractmethod
    def _func(self, X):
        """The method which computes predictions given data. 
        
        NOTE: always set self._filter_columns, which is the
        order in which to extract the data from a pd.dataframe.
    
        :param X: pd.df with columns (Tin, action, Tout, dt, rest of zone temperatures)
        :return predictions as np.array        
        """
        pass

    @abstractmethod
    def fit(self, X, y):
        """Needs to be called to initally fit the model. Will set self._params to coefficients.
        Will refit the model if called with new data.
        :param X: pd.df with columns ('t_in', 'action', 't_out', 'dt') and all zone temperature where all have
        to begin with "zone_temperature_" + "zone name"
        :param y: the labels corresponding to the data. As a pd.dataframe
        :param params: Provide it with the parameters to use/guess. e.g. in constantThermalModel this will be use
        to fit the model 
        :return self
        """
        pass

    @abstractmethod
    def update_fit(self, X, y):
        """Adaptive Learning for given datapoints. The data given will all be given the same weight when learning.
        :param X: (pd.df) with columns ('t_in', 'action', 't_out', 'dt') and all zone temperature where all have 
        to begin with "zone_temperature_" + "zone name
        :param y: (float)
        """
        pass

    # TODO. Give this class a field which tells it what the standard interval prediction is. And given dt to predict
    # TODO continiously predict to nearest multiple.
    def predict(self, X, should_round=False):
        """Predicts the temperatures for each row in X.
        :param X: pd.df/pd.Series with columns ('t_in', 'action', 't_out', 'dt') and all zone temperatures where all
        have to begin with "zone_temperature_" + "zone name"
        :param should_round: bool. Wether to round the prediction according to self.thermal_precision.
        :return (np.array) entry corresponding to prediction of row in X.
        """
        # only predicts next temperatures

        predictions = self._func(X)

        if should_round:
            # NOTE if rounding error occurs it is most likely because the predictions are of type object. So,
            # there must be a bug somewhere in the code.
            # source for rounding: https://stackoverflow.com/questions/2272149/round-to-5-or-other-number-in-python
            predictions = utils.round_increment(predictions, self.thermal_precision)
        else:
            predictions = predictions

        return predictions

    def _RMSE_STD(self, prediction, y):
        '''Computes the RMSE and mean and std of Error.
        NOTE: Use method if you already have predictions.'''
        diff = prediction - y

        mean_error = np.mean(diff)
        rmse = np.sqrt(np.mean(np.square(diff)))
        # standard deviation of the error
        diff_std = np.sqrt(np.mean(np.square(diff - mean_error)))
        return rmse, mean_error, diff_std

    def score(self, X, y, scoreType=-1):
        """Scores the model on the dataset given by X and y.
        :param X: the test_data. pd.df with timeseries data and columns "action", 
        "t_in", "t_out" and "zone_temperatures_*"
        :param y: the expected labels for X. In order of X data.
        :param scoreType: Score on subset of actions that equal scoreType.
        :returns (floats) rmse, mean, std
        """
        # TODO add capabilities to evaluate all heating and all cooling.
        # Filters data to score only on subset of actions.
        assert scoreType in list(range(-1, 6))
        # filter by the action we want to score by
        if scoreType != -1:
            filter_arr = (X['action'] == scoreType)
        elif scoreType == -1:
            filter_arr = np.ones(X['action'].shape) == 1
        X = X[filter_arr]
        y = y[filter_arr]

        # Predict on filtered data
        prediction = self.predict(X, should_round=False)  # only need to predict for relevant actions

        # Get model error
        rmse, mean_error, std = self._RMSE_STD(prediction, y)

        return rmse, mean_error, std