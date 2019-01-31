""" This script cleans a dataframe according to user specifications.

Last modified: November 15 2018

To Do \n
1. For remove_outliers() - may need a different boundary for each column.

Authors \n
@author Marco Pritoni <marco.pritoni@gmail.com>
@author Pranav Gupta <phgupta@ucdavis.edu>

"""

import numpy as np
import pandas as pd
from scipy import stats


class Clean_Data:

    """ This class cleans a dataframe according to user specification """

    def __init__(self, df):
        """ Constructor.
        
        This class stores the original data (passed in through the constructor) and the cleaned data.

        Parameters
        ----------
        df  : pd.DataFrame()
            Dataframe to clean.

        """
        self.original_data = df
        self.cleaned_data = pd.DataFrame()


    def drop_columns(self, col):
        """ Drop columns in dataframe.
        
        Parameters
        ----------
        col     : str
            Column to drop.

        """
        try:
            self.cleaned_data.drop(col, axis=1, inplace=True)
        except Exception as e:
            raise e


    def rename_columns(self, col):
        """ Rename columns of dataframe.
        
        Parameters
        ----------
        col     : list(str)
            List of columns to rename.

        """
        try:
            self.cleaned_data.columns = col
        except Exception as e:
            raise e


    def resample_data(self, data, freq, resampler='mean'):
        """ Resample dataframe.

        Note
        ----
        1. Figure out how to apply different functions to different columns .apply()
        2. This theoretically work in upsampling too, check docs
            http://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.resample.html 

        Parameters
        ----------
        data        : pd.DataFrame()
            Dataframe to resample
        freq        : str
            Resampling frequency i.e. d, h, 15T...
        resampler   : str
            Resampling type i.e. mean, max.

        Returns
        -------
        pd.DataFrame()
            Dataframe containing resampled data

        """

        if resampler == 'mean':
            data = data.resample(freq).mean()
        elif resampler == 'max':
            data = data.resample(freq).max()
        else:
            raise ValueError('Resampler can be \'mean\' or \'max\' only.')
        
        return data


    def interpolate_data(self, data, limit, method):
        """ Interpolate dataframe.

        Parameters
        ----------
        data    : pd.DataFrame()
            Dataframe to interpolate
        limit   : int
            Interpolation limit.
        method  : str
            Interpolation method.

        Returns
        -------
        pd.DataFrame()
            Dataframe containing interpolated data

        """
        data = data.interpolate(how="index", limit=limit, method=method)        
        return data


    def remove_na(self, data, remove_na_how):
        """ Remove NAs from dataframe.

        Parameters
        ----------
        data            : pd.DataFrame()
            Dataframe to remove NAs from.
        remove_na_how   : str
            Specificies how to remove NA i.e. all, any...

        Returns
        -------
        pd.DataFrame()
            Dataframe with NAs removed.

        """
        data = data.dropna(how=remove_na_how)        
        return data


    def remove_outliers(self, data, sd_val):
        """ Remove outliers from dataframe.

        Note
        ----
        1. This function excludes all lines with NA in all columns.

        Parameters
        ----------
        data    : pd.DataFrame()
            Dataframe to remove outliers from.
        sd_val  : int
            Standard Deviation Value (specifices how many SDs away is a point considered an outlier)

        Returns
        -------
        pd.DataFrame()
            Dataframe with outliers removed.

        """
        data = data.dropna()
        data = data[(np.abs(stats.zscore(data)) < float(sd_val)).all(axis=1)]
        return data


    def remove_out_of_bounds(self, data, low_bound, high_bound):
        """ Remove out of bound datapoints from dataframe.

        This function removes all points < low_bound and > high_bound.

        To Do,
        1. Add a different boundary for each column.

        Parameters
        ----------
        data        : pd.DataFrame()
            Dataframe to remove bounds from.
        low_bound   : int
            Low bound of the data.
        high_bound  : int
            High bound of the data.

        Returns
        -------
        pd.DataFrame()
            Dataframe with out of bounds removed.

        """
        data = data.dropna()
        data = data[(data > low_bound).all(axis=1) & (data < high_bound).all(axis=1)]        
        return data


    def clean_data(self, resample=True, freq='h', resampler='mean',
                    interpolate=True, limit=1, method='linear',
                    remove_na=True, remove_na_how='any', 
                    remove_outliers=True, sd_val=3, 
                    remove_out_of_bounds=True, low_bound=0, high_bound=9998):
        """ Clean dataframe.

        Parameters
        ----------
        resample                : bool
            Indicates whether to resample data or not.
        freq                    : str
            Resampling frequency i.e. d, h, 15T...
        resampler               : str
            Resampling type i.e. mean, max.
        interpolate             : bool
            Indicates whether to interpolate data or not.
        limit                   : int
            Interpolation limit.
        method                  : str
            Interpolation method.
        remove_na               : bool
            Indicates whether to remove NAs or not.
        remove_na_how           : str
            Specificies how to remove NA i.e. all, any...
        remove_outliers         : bool
            Indicates whether to remove outliers or not.
        sd_val                  : int
            Standard Deviation Value (specifices how many SDs away is a point considered an outlier)
        remove_out_of_bounds    : bool
            Indicates whether to remove out of bounds datapoints or not.
        low_bound               : int
            Low bound of the data.
        high_bound              : int
            High bound of the data.

        """

        # Store copy of the original data
        data = self.original_data

        if resample:
            try:
                data = self.resample_data(data, freq, resampler)
            except Exception as e:
                raise e

        if interpolate:
            try:
                data = self.interpolate_data(data, limit=limit, method=method)
            except Exception as e:
                raise e
        
        if remove_na:
            try:
                data = self.remove_na(data, remove_na_how)
            except Exception as e:
                raise e

        if remove_outliers:
            try:
                data = self.remove_outliers(data, sd_val)
            except Exception as e:
                raise e

        if remove_out_of_bounds:
            try:
                data = self.remove_out_of_bounds(data, low_bound, high_bound)
            except Exception as e:
                raise e

        self.cleaned_data = data
