""" This script cleans a dataframe according to user specifications.

Note
----
Last modified: Feb 4 2019


To Do
-----
    1. For remove_outlier() - may need a different boundary for each column.
    2. remove_start_NaN() - issues with multi-column df.
    3. Figure out parameter/return types of functions (do a search on "???")


Authors
-------
- Marco Pritoni <marco.pritoni@gmail.com>
- Pranav Gupta <phgupta@ucdavis.edu>

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


    def remove_outlier(self, data, sd_val):
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
                data = self.remove_outlier(data, sd_val)
            except Exception as e:
                raise e

        if remove_out_of_bounds:
            try:
                data = self.remove_out_of_bounds(data, low_bound, high_bound)
            except Exception as e:
                raise e

        self.cleaned_data = data


    ############# Marco's code #############


    def _set_TS_index(self, data):
        """ Convert index to datetime and all other columns to numeric

        Parameters
        ----------
        data    : pd.DataFrame()
            Input dataframe. 

        Returns
        -------
        pd.DataFrame()
            Modified dataframe.

        """
        
        # Set index
        data.index = pd.to_datetime(data.index, error= "ignore")

        # Format types to numeric
        for col in data.columns:
            data[col] = pd.to_numeric(data[col], errors="coerce")

        return data


    def _utc_to_local(self, data, local_zone="America/Los_Angeles"):
        """ Adjust index of dataframe according to timezone that is requested by user.

        Parameters
        ----------
        data        : pd.DataFrame()
            Pandas dataframe of json timeseries response from server.

        local_zone  : str
            pytz.timezone string of specified local timezone to change index to.

        Returns
        -------
        pd.DataFrame()
            Pandas dataframe with timestamp index adjusted for local timezone.
        """

        # Accounts for localtime shift
        data.index = data.index.tz_localize(pytz.utc).tz_convert(local_zone)
        
        # Gets rid of extra offset information so can compare with csv data
        data.index = data.index.tz_localize(None)

        return data


    def _local_to_utc(self, timestamp, local_zone="America/Los_Angeles"):
        """ Convert local timestamp to UTC.

        Parameters
        ----------
        timestamp   : pd.DataFrame()
            Input Pandas dataframe whose index needs to be changed.
        local_zone  : str
            Name of local zone. Defaults to PST.

        Returns
        -------
        pd.DataFrame()
            Dataframe with UTC timestamps.
        
        """

        timestamp_new = pd.to_datetime(timestamp, infer_datetime_format=True, errors='coerce')
        timestamp_new = timestamp_new.tz_localize(local_zone).tz_convert(pytz.utc)
        timestamp_new = timestamp_new.strftime('%Y-%m-%d %H:%M:%S')
        return timestamp_new


    def remove_start_NaN(self, data, var=None):
        """ Remove start NaN.
        
        CHECK: Note issue with multi-column df.
        
        Parameters
        ----------
        data    : pd.DataFrame()
            Input dataframe.
        var     : list(str)
            List that specifies specific columns of dataframe.

        Returns
        -------
        pd.DataFrame()
            Dataframe starting from its first valid index.
       
        """

        # Limit to one or some variables
        if var:
            start_ok_data = data[var].first_valid_index()
        else:
            start_ok_data = data.first_valid_index()
      
        data = data.loc[start_ok_data:, :]
        return data


    def remove_end_NaN(self, data, var=None):
        """ Remove end NaN.
        
        CHECK: Note issue with multi-column df.
        
        Parameters
        ----------
        data    : pd.DataFrame()
            Input dataframe.
        var     : list(str)
            List that specifies specific columns of dataframe.

        Returns
        -------
        pd.DataFrame()
            Dataframe starting from its last valid index.
       
        """
        
        # Limit to one or some variables
        if var:
            end_ok_data = data[var].last_valid_index()
        else:
            end_ok_data = data.last_valid_index()

        data = data.loc[:end_ok_data, :]
        return data


    def _find_missing_return_frame(self, data):
        """ Find missing values in each column of dataframe.

        Parameters
        ----------
        data    : pd.DataFrame()
            Input dataframe.

        Returns
        -------
        pd.DataFrame()
            Dataframe with boolean values indicating if missing data or not.

        """
        return data.isnull()


    def _find_missing(self, data, return_bool=False):
        """ ???

        Parameters
        ----------
        data            : pd.DataFrame()
            Input dataframe.
        return_bool     : bool
            ???

        Returns
        -------
        pd.DataFrame()
            ???

        """

        # This returns the full table with True where the condition is true
        if return_bool == False:
            data = self._find_missing_return_frame(data)
            return data

        # This returns a bool selector if any of the column is True
        elif return_bool == "any":
            bool_sel = self._find_missing_return_frame(data).any(axis=0)
            return bool_sel

        # This returns a bool selector if all of the column are True
        elif return_bool == "all":
            bool_sel = self._find_missing_return_frame(data).all(axis=0)
            return bool_sel
        
        else:
            print("error in multi_col_how input")


    def display_missing(self, data, return_bool="any"):
        """ ???
        
        Parameters
        ----------
        data            : pd.DataFrame()
            Input dataframe.
        return_bool     : bool
            ???

        Returns
        -------
        pd.DataFrame()
            ???

        """

        if return_bool == "any":
            bool_sel = self._find_missing(data, return_bool="any")

        elif return_bool == "all":
            bool_sel = self._find_missing(data, return_bool="all")

        return data[bool_sel]


    def count_missing(self, data, output="number"):
        """ ???
        
        Parameters
        ----------
        data    : pd.DataFrame()
            Input dataframe.
        output  : str
            Sting indicating the output of function (number or percent)

        Returns
        -------
        int/float
            Count of missing data (int or float)

        """

        count = self._find_missing(data,return_bool=False).sum()

        if output == "number":
            return count
        elif output == "percent":
            return ((count / (data.shape[0])) * 100)


    def remove_missing(self, data, return_bool="any"):
        """ ??? 
        
        Parameters
        ----------
        data            : pd.DataFrame()
            Input dataframe.
        return_bool     : bool
            ???

        Returns
        -------
        pd.DataFrame()
            ???

        """

        if return_bool == "any":
            bool_sel = self._find_missing(data,return_bool="any")
        elif return_bool == "all":
            bool_sel = self._find_missing(data,return_bool="all")

        return data[~bool_sel]


    def _find_outOfBound(self, data, lowBound, highBound):
        """ Mask for selecting data that is out of bounds. 
        
        Parameters
        ----------
        data        : pd.DataFrame()
            Input dataframe.
        lowBound    : float
            Lower bound for dataframe.
        highBound   : float
            Higher bound for dataframe.

        Returns
        -------
        ???   

        """

        data = ((data < lowBound) | (data > highBound))
        return data


    def display_outOfBound(self, data, lowBound, highBound):
        """ Select data that is out of bounds. 
        
        Parameters
        ----------
        data        : pd.DataFrame()
            Input dataframe.
        lowBound    : float
            Lower bound for dataframe.
        highBound   : float
            Higher bound for dataframe.

        Returns
        -------
        pd.DataFrame()
            Dataframe containing data that is out of bounds.    

        """

        data = data[self._find_outOfBound(data, lowBound, highBound).any(axis=1)]
        return data


    def count_outOfBound(self, data, lowBound, highBound, output):
        """ Count the number of out of bounds data.
    
        Parameters
        ----------
        data        : pd.DataFrame()
            Input dataframe.
        lowBound    : float
            Lower bound for dataframe.
        highBound   : float
            Higher bound for dataframe.
        output      : str
            Sting indicating the output of function (number or percent)

        Returns
        -------
        int/float
            Count of out of bounds data (int or float)    

        """

        count = self._find_outOfBound(data, lowBound, highBound).sum()
        
        if output == "number":
            return count
        elif output == "percent":
            return count / (data.shape[0]) * 1.0 * 100


    def remove_outOfBound(self, data, lowBound, highBound):
        """ Remove out of bounds data from input dataframe.
    
        Parameters
        ----------
        data        : pd.DataFrame()
            Input dataframe.
        lowBound    : float
            Lower bound for dataframe.
        highBound   : float
            Higher bound for dataframe.

        Returns
        -------
        pd.DataFrame()
            Dataframe with no out of bounds data.    

        """

        data = data[~self._find_outOfBound(data, lowBound, highBound).any(axis=1)]
        return data


    def _calc_outliers_bounds(self, data, method, coeff, window):
        """ Calculate the lower and higher bound for outlier detection.  
        
        Parameters
        ----------
        data        : pd.DataFrame()
            Input dataframe.
        method      : str
            Method to use for calculating the lower and higher bounds.
        coeff       : int
            Coefficient to use in calculation.
        window      : int
            Size of the moving window.

        Returns
        -------
        (float, float)
            Lower and higher bound for detecting outliers.

        """
       
        if method == "std":
            lowBound = (data.mean(axis=0) - coeff * data.std(axis=0)).values[0]
            highBound = (data.mean(axis=0) + coeff * data.std(axis=0)).values[0]

        elif method == "rstd":
            rl_mean=data.rolling(window=window).mean(how=any)
            rl_std = data.rolling(window=window).std(how=any).fillna(method='bfill').fillna(method='ffill')
            
            lowBound = rl_mean - coeff * rl_std
            highBound = rl_mean + coeff * rl_std

        elif method == "rmedian":
            rl_med = data.rolling(window=window, center=True).median().fillna(
                method='bfill').fillna(method='ffill')

            lowBound =  rl_med - coeff
            highBound = rl_med + coeff

        # Coeff is multip for std and IQR or threshold for rolling median
        elif method == "iqr":
            Q1 = data.quantile(.25) # Coeff is multip for std or % of quartile
            Q3 = data.quantile(.75)
            IQR = Q3 - Q1

            lowBound = Q1 - coeff * IQR
            highBound = Q3 + coeff * IQR

        elif method == "qtl":
            lowBound = data.quantile(.005)
            highBound = data.quantile(.995)

        else:
            print ("Method chosen does not exist")
            lowBound = None
            highBound = None

        return lowBound, highBound


    def display_outliers(self, data, method, coeff, window=10):
        """ Returns dataframe with outliers.
        
        Parameters
        ----------
        data        : pd.DataFrame()
            Input dataframe.
        method      : str
            Method to use for calculating the lower and higher bounds.
        coeff       : int
            Coefficient to use in calculation.
        window      : int
            Size of the moving window.

        Returns
        -------
        pd.DataFrame()
            Dataframe containing outliers.

        """
        
        lowBound, highBound = self._calc_outliers_bounds(data, method, coeff, window)
        data = self.display_outOfBound(data, lowBound, highBound)
        return data


    def count_outliers(self, data, method, coeff, output, window=10):
        """ Count the number of outliers in dataframe.
        
        Parameters
        ----------
        data        : pd.DataFrame()
            Input dataframe.
        method      : str
            Method to use for calculating the lower and higher bounds.
        coeff       : int
            Coefficient to use in calculation.
        output      : str
            Sting indicating the output of function (number or percent)
        window      : int
            Size of the moving window.

        Returns
        -------
        int/float
            Count of out of bounds data (int or float)

        """
        
        lowBound, highBound = self._calc_outliers_bounds(data, method, coeff, window)
        count = self.count_outOfBound(data, lowBound, highBound, output=output)
        return count


    def remove_outliers(self, data, method, coeff, window=10):
        """ Remove the outliers in dataframe.
        
        Parameters
        ----------
        data        : pd.DataFrame()
            Input dataframe.
        method      : str
            Method to use for calculating the lower and higher bounds.
        coeff       : int
            Coefficient to use in calculation.
        window      : int
            Size of the moving window.

        Returns
        -------
        pd.DataFrame()
            Dataframe with its outliers removed.

        """
        
        lowBound, highBound = self._calc_outliers_bounds(data, method, coeff, window)
        data = self.remove_outOfBound(data, lowBound, highBound)
        return data


    def _find_equal_to_values(self, data, val):
        """ Mask for selecting data that is equal to val.
        
        Parameters
        ----------
        data        : pd.DataFrame()
            Input dataframe.
        val         : float
            Value.

        Returns
        -------
        ???
            Array of bools - true if equal to val, else false.

        """

        bool_sel = (data == val)
        return bool_sel


    def _find_greater_than_values(self, data, val):
        """ Mask for selecting data that is greater than val.
        
        Parameters
        ----------
        data        : pd.DataFrame()
            Input dataframe.
        val         : float
            Value.

        Returns
        -------
        ???
            Array of bools - true if greater than val, else false.

        """                 
        
        bool_sel = (data > val)   
        return bool_sel


    def _find_less_than_values(self, data, val):
        """ Mask for selecting data that is less than val.
        
        Parameters
        ----------
        data        : pd.DataFrame()
            Input dataframe.
        val         : float
            Value.

        Returns
        -------
        ???
            Array of bools - true if less than val, else false.

        """                     
        
        bool_sel = (data < val)    
        return bool_sel


    def _find_greater_than_or_equal_to_values(self, data, val):
        """ Mask for selecting data that is greater than or equal to val.
        
        Parameters
        ----------
        data        : pd.DataFrame()
            Input dataframe.
        val         : float
            Value.

        Returns
        -------
        ???
            Array of bools - true if greater than or equal to val, else false.

        """  

        bool_sel = (data >= val)  
        return bool_sel


    def _find_less_than_or_equal_to_values(self, data, val):
        """ Mask for selecting data that is less than or equal to val.
        
        Parameters
        ----------
        data        : pd.DataFrame()
            Input dataframe.
        val         : float
            Value.

        Returns
        -------
        ???
            Array of bools - true if less than or equal to val, else false.

        """        
       
        bool_sel = (data <= val)  
        return bool_sel


    def _find_different_from_values(self, data, val):
        """ Mask for selecting data that is not equal to val.
        
        Parameters
        ----------
        data        : pd.DataFrame()
            Input dataframe.
        val         : float
            Value.

        Returns
        -------
        ???
            Array of bools - true if not equal to val, else false.

        """         
        
        bool_sel = ~(data == val)   
        return bool_sel


    def count_if(self, data, condition, val, output="number"):
        """ Count the number of values that match the condition.
        
        Parameters
        ----------
        data        : pd.DataFrame()
            Input dataframe.
        condition   : str
            Condition to match.
        val         : float
            Value to compare against.
        output      : str
            Sting indicating the output of function (number or percent)

        Returns
        -------
        int/float
            Count of values that match the condition (int or float)

        """ 
        
        if condition == "=":
            count = self._find_equal_to_values(data,val).sum()
        elif condition == ">":
            count = self._find_greater_than_values(data,val).sum()
        elif condition == "<":
            count = self._find_less_than_values(data,val).sum()
        elif condition == ">=":
            count = self._find_greater_than_or_equal_to_values(data,val).sum()
        elif condition == "<=":
            count = self._find_less_than_or_equal_to_values(data,val).sum()
        elif condition == "!=":
            count = self._find_different_from_values(data,val).sum()
        
        if output == "number":
            return count
        elif output == "percent":
            return count/data.shape[0]*1.0*100

        return count


    ############# Callie's code #############


    def find_uuid(self, obj, column_name):
        """ Find uuid.

        Parameters
        ----------
        obj             : ???
            the object returned by the MDAL Query
        column_name     : str
            input point returned from MDAL Query

        Returns
        -------
        str 
            the uuid that correlates with the data 

        """

        keys = obj.context.keys()

        for i in keys:
            if column_name in obj.context[i]['?point']:
                uuid = i

        return i


    def identify_missing(self, df, check_start=True):
        """ Identify missing data.

        Parameters
        ----------
        df              : pd.DataFrame()
            Dataframe to check for missing data.
        check_start     : bool
            turns 0 to 1 for the first observation, to display the start of the data
        as the beginning of the missing data event

        Returns
        -------
        pd.DataFrame(), str
            dataframe where 1 indicates missing data and 0 indicates reported data,
        returns the column name generated from the MDAL Query

        """

        # Check start changes the first value of df to 1, when the data stream is initially missing
        # This allows the diff function to acknowledge the missing data
        data_missing = df.isnull() * 1
        col_name = str(data_missing.columns[0])

        # When there is no data stream at the beginning we change it to 1
        if check_start & data_missing[col_name][0] == 1:
            data_missing[col_name][0] = 0

        return data_missing, col_name


    def diff_boolean(self, df, column_name=None, uuid=None, duration=True, min_event_filter='3 hours'):
        """ takes the dataframe of missing values, and returns a dataframe that indicates the 
        length of each event where data was continuously missing

        Parameters
        ----------
        df                  : pd.DataFrame()
            Dataframe to check for missing data (must be in boolean format where 1 indicates missing data. 
        column_name         : str
            the original column name produced by MDAL Query
        uuid                : str
            the uuid associated with the meter, if known
        duration            : bool
            If True, the duration will be displayed in the results. If false the column will be dropped.
        min_event_filter    : str
            Filters out the events that are less than the given time period

        Returns
        -------
        pd.DataFrame()
            dataframe with the start time of the event (as the index),
        end time of the event (first time when data is reported)

        """

        if uuid == None:
            uuid = 'End'

        data_gaps = df[(df.diff() == 1) | (df.diff() == -1)].dropna()
        data_gaps["duration"] = abs(data_gaps.index.to_series().diff(periods=-1))

        data_gaps[uuid] = data_gaps.index + (data_gaps["duration"])

        data_gaps = data_gaps[data_gaps["duration"] > pd.Timedelta(min_event_filter)]
        data_gaps = data_gaps[data_gaps[column_name] == 1]
        data_gaps.pop(column_name)
        if not duration:
            data_gaps.pop('duration')
        data_gaps.index = data_gaps.index.strftime(date_format="%Y-%m-%d %H:%M:%S")
        data_gaps[uuid] = data_gaps[uuid].dt.strftime(date_format="%Y-%m-%d %H:%M:%S")

        return data_gaps


    def analyze_quality_table(self, obj,low_bound=None, high_bound=None):
        """ Takes in an the object returned by the MDAL query, and analyzes the quality 
        of the data for each column in the df. Returns a df of data quality metrics

        To Do
        -----
        Need to make it specific for varying meters and label it for each type,
        Either separate functions or make the function broader

        Parameters
        ----------
        obj             : ???
            the object returned by the MDAL Query

        low_bound       : float
            all data equal to or below this value will be interpreted as missing data
        high_bound      : float
            all data above this value will be interpreted as missing

        Returns
        -------
        pd.DataFrame()
          returns data frame with % missing data, average duration of missing data 
        event and standard deviation of that duration for each column of data

        """

        data = obj.df
        N_rows = 3
        N_cols = data.shape[1]
        d = pd.DataFrame(np.zeros((N_rows, N_cols)),
                         index=['% Missing', 'AVG Length Missing', 'Std dev. Missing'],
                         columns=[data.columns])

        
        if low_bound:
            data = data.where(data >= low_bound)
        if high_bound:
            data=data.where(data < high_bound)


        for i in range(N_cols):

            data_per_meter = data.iloc[:, [i]]

            data_missing, meter = self.identify_missing(data_per_meter)
            percentage = data_missing.sum() / (data.shape[0]) * 100
            data_gaps = self.diff_boolean(data_missing, column_name=meter)

            missing_mean = data_gaps.mean()
            std_dev = data_gaps.std()
            d.loc["% Missing", meter] = percentage[meter]
            d.loc["AVG Length Missing", meter] = missing_mean['duration']
            d.loc["Std dev. Missing", meter] = std_dev['duration']

        return d


    def analyze_quality_graph(self, obj):
        """ Takes in an the object returned by the MDAL query, and analyzes the quality 
        of the data for each column in the df in the form of graphs. The Graphs returned
        show missing data events over time, and missing data frequency during each hour
        of the day

        To Do
        -----
        Need to make it specific for varying meters and label it for each type,
        Either separate functions or make the function broader

        Parameters
        ----------
        obj             : ???
            the object returned by the MDAL Query

        """

        data = obj.df

        for i in range(data.shape[1]):

            data_per_meter = data.iloc[:, [i]]  # need to make this work or change the structure

            data_missing, meter = self.identify_missing(data_per_meter)
            percentage = data_missing.sum() / (data.shape[0]) * 100

            print('Percentage Missing of ' + meter + ' data: ' + str(int(percentage)) + '%')
            data_missing.plot(figsize=(18, 5), x_compat=True, title=meter + " Missing Data over the Time interval")
            data_gaps = self.diff_boolean(data_missing, column_name=meter)

            data_missing['Hour'] = data_missing.index.hour
            ymax = int(data_missing.groupby('Hour').sum().max() + 10)
            data_missing.groupby('Hour').sum().plot(ylim=(0, ymax), figsize=(18, 5),
                                                    title=meter + " Time of Day of Missing Data")

            print(data_gaps)


    #def event_duration(self, obj, dictionary, clean=False, low_bound=None, high_bound=None):
    def event_duration(self, obj, dictionary, low_bound=None, high_bound=None):
        """ Takes in an object and returns a dictionary with the missing data events (start and end)
        for each column in the inputted object (will map to a uuid)

        To Do
        -----
        Need to make it specific for varying meters and label it for each type,
        Either separate functions or make the function broader

        Parameters
        ----------
        obj             : ???
            the object returned by the MDAL Query
        dictionary      : dict
            name of the dictionary
        low_bound       : float
             all data equal to or below this value will be interpreted as missing data
        high_bound      : float
             all data above this value will be interpreted as missing data

        Returns
        -------
        dict
            dictionary with the format:
            {uuid:{start of event 1: end of event 1, start of event 2: end of event 2, ...}, uuid:{..}}

        """

        data = obj.df
        N_cols = data.shape[1]

        if low_bound:
            data = data.where(data >= low_bound)
        if high_bound:
            data=data.where(data < high_bound)

        for i in range(N_cols):

            data_per_meter = data.iloc[:, [i]]

            data_missing, meter = self.identify_missing(data_per_meter)
            uuid = self.find_uuid(obj, column_name=meter)
            data_gaps = self.diff_boolean(data_missing, meter, uuid)

            dictionary_solo = data_gaps.to_dict()
            dictionary[uuid] = dictionary_solo[uuid]
            # dictionary[uuid]=data_gaps # uncomment to get a dictionary of dfs

        return dictionary
