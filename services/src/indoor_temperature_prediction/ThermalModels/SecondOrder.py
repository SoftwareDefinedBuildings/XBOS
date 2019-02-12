
import numpy as np
import pandas as pd

import os, sys
FILE_PATH = os.path.dirname(os.path.abspath(__file__))
xbos_services_path = os.path.dirname(os.path.dirname(os.path.dirname(FILE_PATH)))
sys.path.append(xbos_services_path)
import utils3 as utils
from ParentThermalModel import ParentThermalModel

from scipy.optimize import curve_fit


# following model also works as a sklearn model.
class SecondOrder(ParentThermalModel):
    def __init__(self, interval_thermal, thermal_precision=0.05, learning_rate=0.00001):
        '''
        :param interval_thermal: The minutes the thermal model learns to predict for. The user is responsible to ensure
                                that the data the model receives for training is as specified.
        :param thermal_precision: the closest multiple of which to round to.
        '''

        self._params = None
        self._params_coeff_order = None  # first part of _params is coeff part
        self._params_bias_order = None  # the rest is bias part.
        self._filter_columns = None  # order of columns by which to filter when predicting and fitting data.

        self.thermal_precision = thermal_precision
        self.learning_rate = learning_rate  # TODO evaluate which one is best.

        # Set the parent variables
        super(SecondOrder, self).__init__(thermal_precision, interval_thermal)

    # thermal model function
    def _func(self, X, *params):
        """The polynomial with which we model the thermal model.
        :param X: np.array with row order (Tin, action, Tout, dt, rest of zone temperatures). Is also compatible
                    with pd.df with columns ('t_in', 'action', 't_out', 'dt', "zone_temperatures")
        :param *coeff: the coefficients for the thermal model.
                Should be in order: self._prams_coeff_order, self._params_bias_order
        """
        # Check if we have the right data type.
        if isinstance(X, pd.DataFrame):
            X = X[self._filter_columns].T.as_matrix()
        elif not isinstance(X, np.ndarray):
            raise Exception("_func did not receive a valid datatype. Expects pd.df or np.ndarray")

        if not params:
            try:
                getattr(self, "_params")
            except AttributeError:
                raise RuntimeError("You must train classifier before predicting data!")
            params = self._params

        coeffs = params[:len(self._params_coeff_order)]
        biases = params[len(self._params_coeff_order):]

        features = self._features(X)
        Tin, action = X[0], X[1]

        action_filter = self._filter_actions(X)
        features_biases = (features - biases) * action_filter

        # print("fil",action_filter)
        # print("coeffs", coeffs)
        # print("bias", biases)
        # print("featbias", features_biases)
        # print(X.T)
        return Tin + features_biases.dot(np.array(coeffs))

    def _features(self, X):
        """Returns the features we are using as a matrix.
        :param X: A matrix with row order (Tin, action, Tout, dt, rest of zone temperatures)
        :return np.matrix. each column corresponding to the features in the order of self._param_order"""
        Tin, action, t_last, Tout, dt, zone_temperatures = X[0], X[1], X[2], X[3], X[4], X[5:]
        features = [Tin,  # action == utils.HEATING_ACTION
                    Tin,  # action == utils.COOLING_ACTION
                    Tin - t_last,
                    Tin - Tout,
                    Tin]  # overall bias
        for zone_temp in zone_temperatures:
            features.append(Tin - zone_temp)
        return np.array(features).T

    def _filter_actions(self, X):
        """Returns a matrix of _features(X) shape which tells us which features to use. For example, if we have action Heating,
        we don't want to learn cooling coefficients, so we set the cooling feature to zero.
        :param X: A matrix with row order (Tin, action, Tout, dt, rest of zone temperatures)
        :return np.matrix. each column corresponding to whether to use the features in the order of self._param_order"""
        num_data = X.shape[1]
        action, zone_temperatures = X[1], X[5:]
        action_filter = [action == utils.HEATING_ACTION,
                         action == utils.COOLING_ACTION,
                         np.ones(num_data), # t_last
                         np.ones(num_data),  # tout
                         np.ones(num_data)]  # bias

        for _ in zone_temperatures:
            action_filter.append(np.ones(num_data))

        action_filter = np.array(action_filter).T
        return action_filter

    def fit(self, X, y):
        # TODO how should it update parameters when given more new data?
        """Needs to be called to initally fit the model. Will set self._params to coefficients.
        Will refit the model if called with new data.
        :param X: pd.df with columns ('t_in', 'action', 't_out', 'dt') and all zone temperature where all have
        to begin with "zone_temperature_" + "zone name"
        :param y: the labels corresponding to the data. As a pd.dataframe
        :return self
        """
        zone_col = X.columns[["zone_temperature_" in col for col in X.columns]]
        filter_columns = ['t_in', 'action', 't_last', 't_out', 'dt'] + list(zone_col)

        # give mapping from params to coefficients and to store the order in which we get the columns.
        self._filter_columns = filter_columns
        self._params_coeff_order = ['heating', 'cooling',
                                    'last',
                                    't_out', 'bias'] + list(zone_col)

        self._params_bias_order = ['heating', 'cooling',
                                   'last',
                                   't_out', 'bias'] + list(zone_col)

        # fit the data. we start our guess with all ones for coefficients.
        # Need to do so to be able to generalize to variable number of zones.
        popt, pcov = curve_fit(self._func, X[filter_columns].T.as_matrix(), y.as_matrix(),
                               p0=np.ones(len(
                                   self._params_coeff_order) + len(self._params_bias_order)))
        self._params = np.array(popt)
        return self

    def update_fit(self, X, y):
        # does not fit to the current function anymore.
        raise NotImplementedError("Online Learning is not implemented.")



if __name__ == '__main__':
    pass

