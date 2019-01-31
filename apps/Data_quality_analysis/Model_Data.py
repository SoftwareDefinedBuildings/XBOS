""" This script splits the data into baseline and projection periods, runs models on them and displays metrics & plots.

Last modified: October 30 2018

Authors \n
@author Pranav Gupta <phgupta@ucdavis.edu>

"""

import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.linear_model import LinearRegression, Lasso, Ridge, ElasticNet
from sklearn.ensemble import RandomForestRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import KFold, cross_val_score, train_test_split


class Model_Data:

    """ This class splits the data into baseline and projection periods, runs models on them and displays metrics & plots. 

    Attributes
    ----------
    figure_count    : int
        Keeps track of the number of figures. Primarily useful when using the search function in Wrapper.py.
    
    """

    # Static variable to keep count of number of figures
    figure_count = 1


    def __init__(self, df, input_col, output_col, alphas, cv,
                exclude_time_period, baseline_period, projection_period=None):
        """ Constructor.

        To Do
        -----
        1. Remove alphas as a parameter.

        Parameters
        ----------
        df                      : pd.DataFrame()
            Dataframe to model.
        input_col               : list(str)
            Independent column(s) of dataframe. Defaults to all columns except the last.
        output_col              : str
            Dependent column of dataframe.
        alphas                  : list(int)
            List of alphas to run regression on.
        cv                      : int
            Number of folds for cross-validation. 
        exclude_time_period     : list(str)
            List of time periods to exclude for modeling.
        baseline_period         : list(str)
            List of time periods to split the data into baseline period. It needs to have a start and an end date.
        projection_period       : list(str)
            List of time periods to split the data into projection period. It needs to have a start and an end date.

        """

        self.original_data = df
        self.cv = cv

        if not input_col: # Using all columns except the last as input_col
            input_col = list(self.original_data.columns)
            input_col.remove(output_col)
            self.input_col = input_col
        elif not isinstance(list):
            raise SystemError('Input column should be a list.')
        else:
            self.input_col = input_col

        if not output_col:
            raise SystemError('Please provide the target column.')
        elif not isinstance(output_col, str):
            raise SystemError('Target column should be a string.')
        else:
            self.output_col = output_col

        if not isinstance(alphas, list) and not isinstance(alphas, np.ndarray):
            raise SystemError('alphas should be a list of int\'s or numpy ndarray.')
        else:
            self.alphas = alphas

        if (len(baseline_period) % 2 != 0):
            raise SystemError('baseline period needs to be a multiple of 2 (i.e. have a start and end date)')
        else:
            self.baseline_period = baseline_period
        if exclude_time_period and (len(exclude_time_period) % 2 != 0):
            raise SystemError('exclude time period needs to be a multiple of 2 (i.e. have a start and end date)')
        else:
            self.exclude_time_period = exclude_time_period
        if projection_period and (len(projection_period) % 2 != 0):
            raise SystemError('projection period needs to be a multiple of 2 (i.e. have a start and end date)')
        else:
            self.projection_period = projection_period

        self.baseline_in        = pd.DataFrame()    # Baseline's indepndent columns
        self.baseline_out       = pd.DataFrame()    # Baseline's dependent column

        self.best_model         = None              # Best Model
        self.best_model_name    = None              # Best Model's name
        self.y_pred             = pd.DataFrame()    # Best Model's predictions
        self.y_true             = pd.DataFrame()    # Testing set's true values
        self.best_metrics       = {}

        self.models             = []                # List of models
        self.model_names        = []                # List of model names
        self.max_scores         = []                # List of max scores of each model
        self.metrics            = {}                # Each model's metrics


    def split_data(self):
        """ Split data according to baseline and projection time period values """

        try:
            # Extract data ranging in time_period1
            time_period1 = (slice(self.baseline_period[0], self.baseline_period[1]))
            self.baseline_in = self.original_data.loc[time_period1, self.input_col]
            self.baseline_out = self.original_data.loc[time_period1, self.output_col]

            if self.exclude_time_period:
                for i in range(0, len(self.exclude_time_period), 2):
                    # Drop data ranging in exclude_time_period1
                    exclude_time_period1 = (slice(self.exclude_time_period[i], self.exclude_time_period[i+1]))
                    self.baseline_in.drop(self.baseline_in.loc[exclude_time_period1].index, axis=0, inplace=True)
                    self.baseline_out.drop(self.baseline_out.loc[exclude_time_period1].index, axis=0, inplace=True)
        except Exception as e:
            raise e

        # CHECK: Can optimize this part
        # Error checking to ensure time_period values are valid
        if self.projection_period:
            for i in range(0, len(self.projection_period), 2):
                period = (slice(self.projection_period[i], self.projection_period[i+1]))
                try:
                    self.original_data.loc[period, self.input_col]
                    self.original_data.loc[period, self.output_col]
                except Exception as e:
                    raise e


    def adj_r2(self, r2, n, k):
        """ Calculate and return adjusted r2 score.

        Parameters
        ----------
        r2  :
            Original r2 score.
        n   :
            Number of points in data sample.
        k   :
            Number of variables in model, excluding the constant.

        Returns
        -------
        float
            Adjusted R2 score.

        """
        return 1 - (((1 - r2) * (n - 1)) / (n - k - 1))


    def linear_regression(self):
        """ Linear Regression.

        This function runs linear regression and stores the, 
        1. Model
        2. Model name 
        3. Mean score of cross validation
        4. Metrics

        """

        model = LinearRegression()
        scores = []

        kfold = KFold(n_splits=self.cv, shuffle=True, random_state=42)
        for i, (train, test) in enumerate(kfold.split(self.baseline_in, self.baseline_out)):
            model.fit(self.baseline_in.iloc[train], self.baseline_out.iloc[train])
            scores.append(model.score(self.baseline_in.iloc[test], self.baseline_out.iloc[test]))

        mean_score = sum(scores) / len(scores)
        
        self.models.append(model)
        self.model_names.append('Linear Regression')
        self.max_scores.append(mean_score)

        self.metrics['Linear Regression'] = {}
        self.metrics['Linear Regression']['R2'] = mean_score
        self.metrics['Linear Regression']['Adj R2'] = self.adj_r2(mean_score, self.baseline_in.shape[0], self.baseline_in.shape[1])


    def lasso_regression(self):
        """ Lasso Regression.

        This function runs lasso regression and stores the,
        1. Model
        2. Model name
        3. Max score
        4. Metrics

        """

        score_list = []
        max_score = float('-inf')
        best_alpha = None

        for alpha in self.alphas:
            # model = Lasso(normalize=True, alpha=alpha, max_iter=5000)
            model = Lasso(alpha=alpha, max_iter=5000)
            model.fit(self.baseline_in, self.baseline_out.values.ravel())

            scores = []
            kfold = KFold(n_splits=self.cv, shuffle=True, random_state=42)
            for i, (train, test) in enumerate(kfold.split(self.baseline_in, self.baseline_out)):
                model.fit(self.baseline_in.iloc[train], self.baseline_out.iloc[train])
                scores.append(model.score(self.baseline_in.iloc[test], self.baseline_out.iloc[test]))
            mean_score = np.mean(scores)

            score_list.append(mean_score)
            
            if mean_score > max_score:
                max_score = mean_score
                best_alpha = alpha

        # self.models.append(Lasso(normalize=True, alpha=best_alpha, max_iter=5000))
        self.models.append(Lasso(alpha=best_alpha, max_iter=5000))
        self.model_names.append('Lasso Regression')
        self.max_scores.append(max_score)
        
        self.metrics['Lasso Regression'] = {}
        self.metrics['Lasso Regression']['R2'] = max_score
        self.metrics['Lasso Regression']['Adj R2'] = self.adj_r2(max_score, self.baseline_in.shape[0], self.baseline_in.shape[1])


    def ridge_regression(self):
        """ Ridge Regression.

        This function runs ridge regression and stores the,
        1. Model
        2. Model name
        3. Max score
        4. Metrics

        """

        score_list = []
        max_score = float('-inf')
        best_alpha = None

        for alpha in self.alphas:
            # model = Ridge(normalize=True, alpha=alpha, max_iter=5000)
            model = Ridge(alpha=alpha, max_iter=5000)
            model.fit(self.baseline_in, self.baseline_out.values.ravel())

            scores = []
            kfold = KFold(n_splits=self.cv, shuffle=True, random_state=42)
            for i, (train, test) in enumerate(kfold.split(self.baseline_in, self.baseline_out)):
                model.fit(self.baseline_in.iloc[train], self.baseline_out.iloc[train])
                scores.append(model.score(self.baseline_in.iloc[test], self.baseline_out.iloc[test]))
            mean_score = np.mean(scores)

            score_list.append(mean_score)
            
            if mean_score > max_score:
                max_score = mean_score
                best_alpha = alpha

        # self.models.append(Ridge(normalize=True, alpha=best_alpha, max_iter=5000))
        self.models.append(Ridge(alpha=best_alpha, max_iter=5000))
        self.model_names.append('Ridge Regression')
        self.max_scores.append(max_score)
        
        self.metrics['Ridge Regression'] = {}
        self.metrics['Ridge Regression']['R2'] = max_score
        self.metrics['Ridge Regression']['Adj R2'] = self.adj_r2(max_score, self.baseline_in.shape[0], self.baseline_in.shape[1])


    def elastic_net_regression(self):
        """ ElasticNet Regression.

        This function runs elastic net regression and stores the,
        1. Model
        2. Model name
        3. Max score
        4. Metrics

        """

        score_list = []
        max_score = float('-inf')
        best_alpha = None

        for alpha in self.alphas:
            # CHECK: tol value too large?
            # model = ElasticNet(normalize=True, alpha=alpha, max_iter=5000, tol=0.01)
            model = ElasticNet(alpha=alpha, max_iter=5000, tol=0.01)            
            model.fit(self.baseline_in, self.baseline_out.values.ravel())

            scores = []
            kfold = KFold(n_splits=self.cv, shuffle=True, random_state=42)
            for i, (train, test) in enumerate(kfold.split(self.baseline_in, self.baseline_out)):
                model.fit(self.baseline_in.iloc[train], self.baseline_out.iloc[train])
                scores.append(model.score(self.baseline_in.iloc[test], self.baseline_out.iloc[test]))
            mean_score = np.mean(scores)

            score_list.append(mean_score)
            
            if mean_score > max_score:
                max_score = mean_score
                best_alpha = alpha

        # CHECK: tol value too large?
        # self.models.append(ElasticNet(normalize=True, alpha=best_alpha, max_iter=5000, tol=0.01))
        self.models.append(ElasticNet(alpha=best_alpha, max_iter=5000, tol=0.01))
        self.model_names.append('ElasticNet Regression')
        self.max_scores.append(max_score)
        

        self.metrics['ElasticNet Regression'] = {}
        self.metrics['ElasticNet Regression']['R2'] = max_score
        self.metrics['ElasticNet Regression']['Adj R2'] = self.adj_r2(max_score, self.baseline_in.shape[0], self.baseline_in.shape[1])


    def random_forest(self):
        """ Random Forest.

        This function runs random forest and stores the,
        1. Model
        2. Model name
        3. Max score
        4. Metrics

        """

        model = RandomForestRegressor(random_state=42)

        scores = []
        kfold = KFold(n_splits=self.cv, shuffle=True, random_state=42)
        for i, (train, test) in enumerate(kfold.split(self.baseline_in, self.baseline_out)):
            model.fit(self.baseline_in.iloc[train], self.baseline_out.iloc[train])
            scores.append(model.score(self.baseline_in.iloc[test], self.baseline_out.iloc[test]))
        mean_score = np.mean(scores)

        self.models.append(model)
        self.model_names.append('Random Forest Regressor')
        self.max_scores.append(mean_score)
        
        self.metrics['Random Forest Regressor'] = {}
        self.metrics['Random Forest Regressor']['R2'] = mean_score
        self.metrics['Random Forest Regressor']['Adj R2'] = self.adj_r2(mean_score, self.baseline_in.shape[0], self.baseline_in.shape[1])


    def ann(self):
        """ Artificial Neural Network.

        This function runs ANN and stores the,
        1. Model
        2. Model name
        3. Max score
        4. Metrics

        """
        
        model = MLPRegressor()

        scores = []
        kfold = KFold(n_splits=self.cv, shuffle=True, random_state=42)
        for i, (train, test) in enumerate(kfold.split(self.baseline_in, self.baseline_out)):
            model.fit(self.baseline_in.iloc[train], self.baseline_out.iloc[train])
            scores.append(model.score(self.baseline_in.iloc[test], self.baseline_out.iloc[test]))
        mean_score = np.mean(scores)

        self.models.append(model)
        self.model_names.append('Artificial Neural Network')
        self.max_scores.append(mean_score)
        
        self.metrics['Artificial Neural Network'] = {}
        self.metrics['Artificial Neural Network']['R2'] = mean_score
        self.metrics['Artificial Neural Network']['Adj R2'] = self.adj_r2(mean_score, self.baseline_in.shape[0], self.baseline_in.shape[1])

  
    def run_models(self):
        """ Run all models.

        Returns
        -------
        model
            Best model
        dict
            Metrics of the models

        """

        self.linear_regression()
        self.lasso_regression()
        self.ridge_regression()
        self.elastic_net_regression()
        self.random_forest()
        self.ann()

        # Index of the model with max score
        best_model_index = self.max_scores.index(max(self.max_scores))

        # Store name of the optimal model
        self.best_model_name = self.model_names[best_model_index]

        # Store optimal model
        self.best_model = self.models[best_model_index]

        return self.metrics


    def custom_model(self, func):
        """ Run custom model provided by user.

        To Do,
        1. Define custom function's parameters, its data types, and return types

        Parameters
        ----------
        func    : function
            Custom function

        Returns
        -------
        dict
            Custom function's metrics

        """

        y_pred = func(self.baseline_in, self.baseline_out)

        self.custom_metrics = {}
        self.custom_metrics['r2'] = r2_score(self.baseline_out, y_pred)
        self.custom_metrics['mse'] = mean_squared_error(self.baseline_out, y_pred)
        self.custom_metrics['rmse'] = math.sqrt(self.custom_metrics['mse'])
        self.custom_metrics['adj_r2'] = self.adj_r2(self.custom_metrics['r2'], self.baseline_in.shape[0], self.baseline_in.shape[1])

        return self.custom_metrics


    def best_model_fit(self):
        """ Fit data to optimal model and return its metrics.

        Returns
        -------
        dict
            Best model's metrics

        """

        # X_train, X_test, y_train, y_test = train_test_split(self.baseline_in, self.baseline_out, 
        #                                                     test_size=0.30, random_state=42)

        # self.best_model.fit(X_train, y_train)
        # self.y_true = y_test                        # Pandas Series
        # self.y_pred = self.best_model.predict(X_test)    # numpy.ndarray

        # # Set all negative values to zero since energy > 0
        # self.y_pred[self.y_pred < 0] = 0
        
        # # n and k values for adj r2 score
        # self.n_test = X_test.shape[0]   # Number of points in data sample
        # self.k_test = X_test.shape[1]   # Number of variables in model, excluding the constant

        # # Store best model's metrics
        # self.best_metrics['name']   = self.best_model_name
        # self.best_metrics['r2']     = r2_score(self.y_true, self.y_pred)
        # self.best_metrics['mse']    = mean_squared_error(self.y_true, self.y_pred)
        # self.best_metrics['rmse']   = math.sqrt(self.best_metrics['mse'])
        # self.best_metrics['adj_r2'] = self.adj_r2(self.best_metrics['r2'], self.n_test, self.k_test)

        # # Normalized Mean Bias Error
        # numerator = sum(self.y_true - self.y_pred)
        # denominator = (self.n_test - self.k_test) * (sum(self.y_true) / len(self.y_true))
        # self.best_metrics['nmbe'] = numerator / denominator

        # return self.best_metrics

        self.best_model.fit(self.baseline_in, self.baseline_out)

        self.y_true = self.baseline_out                             # Pandas Series
        self.y_pred = self.best_model.predict(self.baseline_in)     # numpy.ndarray

        # Set all negative values to zero since energy > 0
        self.y_pred[self.y_pred < 0] = 0

        # n and k values for adj r2 score
        self.n_test = self.baseline_in.shape[0]   # Number of points in data sample
        self.k_test = self.baseline_in.shape[1]   # Number of variables in model, excluding the constant

        # Store best model's metrics
        self.best_metrics['name']   = self.best_model_name
        self.best_metrics['r2']     = r2_score(self.y_true, self.y_pred)
        self.best_metrics['mse']    = mean_squared_error(self.y_true, self.y_pred)
        self.best_metrics['rmse']   = math.sqrt(self.best_metrics['mse'])
        self.best_metrics['adj_r2'] = self.adj_r2(self.best_metrics['r2'], self.n_test, self.k_test)

        # Normalized Mean Bias Error
        numerator = sum(self.y_true - self.y_pred)
        denominator = (self.n_test - self.k_test) * (sum(self.y_true) / len(self.y_true))
        self.best_metrics['nmbe']   = numerator / denominator


        # MAPE can't have 0 values in baseline_out -> divide by zero error
        self.baseline_out_copy  = self.baseline_out[self.baseline_out != 0]
        self.baseline_in_copy   = self.baseline_in[self.baseline_in.index.isin(self.baseline_out_copy.index)]
        self.y_true_copy = self.baseline_out_copy                             # Pandas Series
        self.y_pred_copy = self.best_model.predict(self.baseline_in_copy)     # numpy.ndarray
        self.best_metrics['mape']   = np.mean(np.abs((self.y_true_copy - self.y_pred_copy) / self.y_true_copy)) * 100

        return self.best_metrics
