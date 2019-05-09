
import numpy as np
import pandas as pd
import itertools

import os, sys
FILE_PATH = os.path.dirname(os.path.abspath(__file__))
xbos_services_path = os.path.dirname(os.path.dirname(os.path.dirname(FILE_PATH)))
sys.path.append(xbos_services_path)
import utils3 as utils
from ParentThermalModel import ParentThermalModel

from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import RandomizedSearchCV


class RandomForest(ParentThermalModel):
    # how many coefficient we want to learn for start and end of convolution for each action. HYPERPARAMETER
    NUM_START = 4
    NUM_END = 4

    TWO_STAGES = False

    def __init__(self, interval_thermal, thermal_precision=0.05, learning_rate=0.00001):
        '''
        :param interval_thermal: The minutes the thermal model learns to predict for. The user is responsible to ensure
                                that the data the model receives for training is as specified.
        :param thermal_precision: the closest multiple of which to round to.
        '''
        self._regr = None
        self._filter_columns = None  # order of columns by which to filter when predicting and fitting data.
        self.thermal_precision = thermal_precision
        super(RandomForest, self).__init__(thermal_precision, interval_thermal)

    def fit(self, X, y, hype_search=False):
        """Needs to be called to initally fit the model.
        Will set self._params to coefficients.
        Will refit the model if called with new data.
        :param X: pd.df with columns ('t_in', 'action', 'previous_action', 'action_duration', 't_out', 'dt') and all zone temperature where all have
        to begin with "zone_temperature_" + "zone name"
        :param y: the labels corresponding to the data. As a pd.dataframe
        :param hype_search: whether to run hyperparameter search
        :return self
        """

        # set column order
        zone_col = X.columns[["zone_temperature_" in col for col in X.columns]]
        filter_columns = ['t_in', 'action', 'previous_action', 'action_duration', 't_last', 't_out', 'occ', 'dt'] + list(zone_col)
        self._filter_columns = filter_columns

        # set feature order
        if not RandomForest.TWO_STAGES:
            actions_order = [act + "_" + "start" + "_" + str(num) for act, num in itertools.product(["heating", "cooling"], list(range(RandomForest.NUM_START)))]
            actions_order += [act + "_" + "end" + "_" + str(num) for act, num in itertools.product(["heating", "cooling"], list(range(RandomForest.NUM_END)))]

            self._feature_order = actions_order + ['t_last', 't_out', 'no_action', 'occ'] + list(zone_col)
        else:
            raise NotImplementedError("Two stage thermal model is not implemented.")

        features = self._features(X[filter_columns].T.as_matrix())
        y = y - X["t_in"].values

        self._regr = RandomForestRegressor()  # TODO check hyperparameters

        # fit the data.
        if not hype_search:
            self._regr.fit(features, y.as_matrix())
        else:
            self._regr = self.hyperparameter_search(features, y.as_matrix())
        return self

    def hyperparameter_search(self, X, y):
        """Does hyperparameter search on random forest with given data and predefined hyperparameter space.
        :param X: np Feature matrix.
        :param y: np the labels corresponding to the data.
        :return Trained RandomizedSearchCV object.
        """
        # Number of trees in random forest
        n_estimators = [int(x) for x in np.linspace(start=200, stop=2000, num=10)]
        # Number of features to consider at every split
        max_features = ['auto', 'sqrt']
        # Maximum number of levels in tree
        max_depth = [int(x) for x in np.linspace(10, 110, num=11)]
        max_depth.append(None)
        # Minimum number of samples required to split a node
        min_samples_split = [2, 5, 10]
        # Minimum number of samples required at each leaf node
        min_samples_leaf = [1, 2, 4]
        # Method of selecting samples for training each tree
        bootstrap = [True, False]
        # Create the random grid
        random_grid = {'n_estimators': n_estimators,
                       'max_features': max_features,
                       'max_depth': max_depth,
                       'min_samples_split': min_samples_split,
                       'min_samples_leaf': min_samples_leaf,
                       'bootstrap': bootstrap}

        # Use the random grid to search for best hyperparameters

        # Random search of parameters, using 3 fold cross validation,
        # search across 100 different combinations, and use all available cores
        rf_random = RandomizedSearchCV(estimator=self._regr, param_distributions=random_grid, n_iter=33, cv=3, verbose=2,
                                       random_state=42, n_jobs=-1)
        # Fit the random search model
        rf_random.fit(X, y)

        return rf_random.best_estimator_

    # thermal model function
    def _func(self, X):
        """Predicts with trained model.
        :param X: - np.array with row order according to self._filter_columns
                  - pd.df with columns according to self._filter_columns
        """
        if isinstance(X, pd.DataFrame):
            X = X[self._filter_columns].T.as_matrix()
        elif not isinstance(X, np.ndarray):
            raise Exception("_func did not receive a valid datatype. Expects pd.df or np.ndarray")

        if self._regr is None:
            raise RuntimeError("You must train classifier before predicting data!")

        regr = self._regr
        features = self._features(X)

        return X[0] + regr.predict(features)

    def _features(self, X):
        """Returns the features we are using as a matrix.
        :param X: A matrix with row order self._filter_columns
        :return np.matrix. each column corresponding to the features in the order of self._param_order"""

        Tin, action, previous_action, action_duration, Tlast, Tout, occ, dt, zone_temperatures = X[0], X[1], X[2], X[3], X[4], X[5], X[6], X[7], X[8:]
        features = []

        if not RandomForest.TWO_STAGES:
            NUM_ACTIONS = 2  # heating and cooling
            features += [Tin for _ in range(NUM_ACTIONS*RandomForest.NUM_START + NUM_ACTIONS*RandomForest.NUM_END)]

        else:
            raise NotImplementedError("Two stage thermal model is not implemented.")

        features.append(Tin - Tlast)
        features.append(Tin - Tout)  # outside temperature influence.
        features.append(Tin)  # no action (overall bias)
        features.append(Tin)  # occupancy

        for zone_temp in zone_temperatures:
            features.append(Tin - zone_temp)

        features = np.array(features).T
        action_filter = self._filter_actions(X)
        features = features * action_filter

        return features

    def _filter_actions(self, X):
        """Returns a matrix of _features(X) shape which tells us which features to use. For example, if we have action Heating,
        we don't want to learn cooling coefficients, so we set the cooling feature to zero.
        :param X: A matrix with row order (Tin, action, Tout, dt, rest of zone temperatures)
        :return np.matrix. each column corresponding to whether to use the features in the order of self._param_order"""

        num_data = X.shape[1]
        action, previous_action, action_duration, occ, dt, zone_temperatures = X[1], X[2], X[3], X[6], X[7], X[8:]

        action_filter = []

        # setting action filter according to convolution properties.
        for iter_action, iter_num_start in itertools.product([utils.HEATING_ACTION, utils.COOLING_ACTION], list(range(RandomForest.NUM_START))):
            if iter_num_start != RandomForest.NUM_START - 1:
                action_filter += [(action == iter_action) & (((action_duration - dt) // self.interval_thermal) == iter_num_start)]
            else:
                action_filter += [(action == iter_action) & (((action_duration - dt) // self.interval_thermal) >= iter_num_start)]

        for iter_action, iter_num_end in itertools.product([utils.HEATING_ACTION, utils.COOLING_ACTION], list(range(RandomForest.NUM_END))):
            if iter_num_end != RandomForest.NUM_END - 1:
                action_filter += [(previous_action == iter_action) & (((action_duration - dt) // self.interval_thermal) == iter_num_end)]
            else:
                action_filter += [(previous_action == iter_action) & (((action_duration - dt) // self.interval_thermal) >= iter_num_end)]

        action_filter += [np.ones(num_data),  # t_last
                        np.ones(num_data),  # tout
                         np.ones(num_data),  # bias/no action
                          occ]

        # other zones
        for _ in zone_temperatures:
            action_filter.append(np.ones(num_data))

        action_filter = np.array(action_filter).T
        return action_filter

    def update_fit(self, X, y):
        raise NotImplementedError("Online Learning is not implemented.")

    def save_tree(self):

        # Import tools needed for visualization
        from sklearn.tree import export_graphviz
        import pydot
        # Pull out one tree from the forest
        tree = self._regr.estimators_[5]
        # Export the image to a dot file
        export_graphviz(tree, out_file='tree.dot', feature_names=self._feature_order, rounded=True, precision=1)
        # Use dot file to create a graph
        (graph,) = pydot.graph_from_dot_file('tree.dot')
        # Write graph to a png file
        graph.write_png('tree.png')

if __name__ == '__main__':
    import pickle
    import datetime

    path = "../Data/"
    building = "avenal-animal-shelter"
    interval = 5  # min

    with open(path + building + "_training_data.pkl", "r") as f:
        training_data = pickle.load(f)

    with open(path + building + "_test_data.pkl", "r") as f:
        test_data = pickle.load(f)


    def add_last_temperature_feature(data):
        """Adding a feature which specifies what the previous temperature was "dt" seconds before the current
        datasample. Since data does not need be continious, we need a loop.
        :param: pd.df with cols: "t_in", "dt" and needs to be sorted by time.
        returns pd.df with cols "t_last" added. """

        last_temps = []

        last_temp = None
        curr_time = data.index[0]
        for index, row in data.iterrows():

            if last_temp is None:
                last_temps.append(row["t_in"])  # so the feature will be zero instead
            else:
                last_temps.append(last_temp)

            if curr_time == index:
                last_temp = row["t_in"]
                curr_time += datetime.timedelta(minutes=row["dt"])
            else:
                last_temp = None
                curr_time = index + datetime.timedelta(minutes=row["dt"])

        data["t_last"] = np.array(last_temps)
        return data


    training_data = add_last_temperature_feature(training_data)
    test_data = add_last_temperature_feature(test_data)


    def fix_it(data, interval):

        def f(x):
            if x == 0:
                return 0
            elif x == 2 or x == 5:
                return 2
            elif x == 1 or x == 3:
                return 1

        data["action"] = data["action"].map(f)
        data["action_duration"] = data["action_duration"].map(lambda x: utils.get_window_in_sec(str(x)) / 60.)
        data = data.fillna(-1)  # Assumes only column with nan values is previous action.
        # Previous action with -1 is counted as if no action happened before.

        before_drop = data.shape
        data = data.dropna()
        if data.shape[0] != before_drop[0]:
            print("WARNING: Dopped nans")

        return data, data[data["dt"] == interval]


    org_training_data, training_data = fix_it(training_data, interval)
    org_test_data, test_data = fix_it(test_data, interval)

    random_forest = RandomForest(interval).fit(training_data, training_data["t_next"])

    print("Training data")
    print("Random Forest", random_forest.score(training_data, training_data["t_next"]))

    print("Test data")
    print("Random Forest", random_forest.score(test_data, test_data["t_next"]))


