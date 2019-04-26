""" This script is a wrapper class around all the other modules - importing, cleaning, preprocessing and modeling the data.

Note
----
Last modified: Feb 4 2019

1. For MAPE, all rows with 0 are dropped in baseline_out.
2. df.loc[(slice(None, None, None)), ...] is equivalent to "df.loc[:,...]"
3. df.resample(freq='h').mean() drops all non-float/non-int columns
4. os._exit(1) exits the program without calling cleanup handlers.
5. Add sys.path.append("..") in Jupyter notebooks for all the imports to work.


To Do
-----
1. Import
    1. Check if file_name or folder_name is of type unicode -> convert to string.
2. Clean
    1. Clean each column differently.
    2. Test all functions from TS_Util.py
3. Model
    1. Add param_dict parameter.
    2. For baseline/projection period, if no start/end date, use first/last row.
    3. Save best model.
    4. Add SVR, ANN.
4. Wrapper
    1. Give user the option to run specific models.
    2. Change search()
5. All
    1. Look into adding other plots.
    2. Check if Python2.7 works.
    3. Change conf.py's absolute path.
6. Cleanup
    1. Pylint.
    2. Documentation.
    3. Unit Tests.
    4. Docker.
    5. Update Energy_Analytics, XBOS_Data_Analytics, XBOS.


Authors
-------
- Pranav Gupta <phgupta@ucdavis.edu>

"""

import os
import json
import datetime
import numpy as np
import pandas as pd
from scipy import stats
from datetime import date



from Import_Data import Import_Data, Import_MDAL
from Clean_Data import Clean_Data
from Preprocess_Data import Preprocess_Data
from Model_Data import Model_Data
from Plot_Data import Plot_Data


class Wrapper:

    """ This class is a wrapper class around all the other modules - importing, cleaning, preprocessing and modeling the data.

    Attributes
    ----------
    figure_count    : int
        Keeps track of the number of iterations when searching for optimal model. Primarily used in search function.

    """

    # Static variable to keep count of number of iterations
    global_count = 1


    def __init__(self, results_folder_name='results', site_name='Undefined'):
        """ Constructor.

        Initializes variables and creates results directory.

        Parameters
        ----------
        results_folder_name     : str
            Name of folder where results will reside

        """

        self.results_folder_name    = results_folder_name
        self.result                 = {}                    # Dictionary containing all the metrics
        self.best_metrics           = {}                    # Metrics of optimal model
        
        self.imported_data          = pd.DataFrame()
        self.cleaned_data           = pd.DataFrame()
        self.preprocessed_data      = pd.DataFrame()
        self.project_df             = pd.DataFrame()

        # Create instance of Plot_Data 
        self.plot_data_obj          = Plot_Data()
        
        # Store UTC Time
        self.result['Time (UTC)']   = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

        # Store site name
        self.result['Site'] = site_name

        # Create results folder if it doesn't exist
        if not os.path.isdir(self.results_folder_name):
            os.makedirs(self.results_folder_name)


    def get_global_count(self):
        """ Return global count (used for naming of .json and .png files) 

        Returns
        -------
        int
            Global count

        """
        
        # Check current number of json files in results directory and dump current json in new file
        path_to_json = self.results_folder_name + '/'
        json_files = [pos_json for pos_json in os.listdir(path_to_json) if pos_json.endswith('.json')]
        Wrapper.global_count = len(json_files) + 1
        return Wrapper.global_count


    def add_comments(self, dic):
        """ Add comments to results json file.

        dic     : dict
            Dictionary of key,value pairs added to result

        """

        self.result['User Comments'] = {}
        self.result['User Comments'].update(dic)


    def write_json(self):
        """ Dump data into json file. """

        with open(self.results_folder_name + '/results-' + str(self.get_global_count()) + '.json', 'a') as f:
            json.dump(self.result, f)


    def site_analysis(self, folder_name, site_install_mapping, end_date):
        """ Summarize site data into a single table.

        folder_name         : str
            Folder where all site data resides.
        site_event_mapping  : dic
            Dictionary of site name to date of installation.
        end_date            : str
            End date of data collected.

        """

        def count_number_of_days(site, end_date):
            """ Counts the number of days between two dates.

            Parameters
            ----------
            site        : str
                Key to a dic containing site_name -> pelican installation date.
            end_date    : str
                End date.

            Returns
            -------
            int
                Number of days

            """
            
            start_date = site_install_mapping[site]
            start_date = start_date.split('-')
            start = date(int(start_date[0]), int(start_date[1]), int(start_date[2]))
            
            end_date = end_date.split('-')
            end = date(int(end_date[0]), int(end_date[1]), int(end_date[2]))
            
            delta = end - start
            return delta.days


        if not folder_name or not isinstance(folder_name, str):
            raise TypeError("folder_name should be type string")
        else:
            list_json_files = []
            df      = pd.DataFrame()
            temp_df = pd.DataFrame()
            json_files = [f for f in os.listdir(folder_name) if f.endswith('.json')]
            
            for json_file in json_files:
                
                with open(folder_name + json_file) as f:
                    js = json.load(f)
                    num_days = count_number_of_days(js['Site'], end_date)
                
                    e_abs_sav = round(js['Energy Savings (absolute)'] / 1000, 2) # Energy Absolute Savings
                    e_perc_sav = round(js['Energy Savings (%)'], 2) # Energy Percent Savings
                    ann_e_abs_sav = (e_abs_sav / num_days) * 365 # Annualized Energy Absolute Savings
                    
                    d_abs_sav = round(js['User Comments']['Dollar Savings (absolute)'], 2) # Dollar Absolute Savings
                    d_perc_sav = round(js['User Comments']['Dollar Savings (%)'], 2) # Dollar Percent Savings
                    ann_d_abs_sav = (d_abs_sav / num_days) * 365 # Annualized Dollar Absolute Savings

                    temp_df = pd.DataFrame({
                        'Site': js['Site'],
                        '#Days since Pelican Installation': num_days,

                        'Energy Savings (%)': e_perc_sav,
                        'Energy Savings (kWh)': e_abs_sav,
                        'Annualized Energy Savings (kWh)': ann_e_abs_sav,
                        
                        'Dollar Savings (%)': d_perc_sav,
                        'Dollar Savings ($)': d_abs_sav,
                        'Annualized Dollar Savings ($)': ann_d_abs_sav,
                        
                        'Best Model': js['Model']['Optimal Model\'s Metrics']['name'],
                        'Adj R2': round(js['Model']['Optimal Model\'s Metrics']['adj_cross_val_score'], 2),
                        
                        'RMSE': round(js['Model']['Optimal Model\'s Metrics']['rmse'], 2),
                        'MAPE': js['Model']['Optimal Model\'s Metrics']['mape'],
                        'Uncertainity': js['Uncertainity'],
                    }, index=[0])
                
                df = df.append(temp_df)

            df.set_index('Site', inplace=True)
            return df


    def read_json(self, file_name=None, input_json=None, imported_data=pd.DataFrame()):
        """ Read input json file.

        Notes
        -----
        The input json file should include ALL parameters.

        Parameters
        ----------
        file_name   : str
            Filename to be read.
        input_json  : dict
            JSON object to be read.
        imported_data   : pd.DataFrame()
            Pandas Dataframe containing data.

        """

        if not file_name and not input_json or file_name and input_json:
            raise TypeError('Provide either json file or json object to read.')
        
        # Read json file
        if file_name:
            if not isinstance(file_name, str) or not file_name.endswith('.json') or not os.path.isfile('./'+file_name):
                raise TypeError('File name should be a valid .json file residing in current directory.')
            else:
                f = open(file_name)
                input_json = json.load(f)

        if imported_data.empty:
            import_json = input_json['Import']
            imported_data = self.import_data(file_name=import_json['File Name'], folder_name=import_json['Folder Name'],
                                            head_row=import_json['Head Row'], index_col=import_json['Index Col'],
                                            convert_col=import_json['Convert Col'], concat_files=import_json['Concat Files'],
                                            save_file=import_json['Save File'])

        clean_json = input_json['Clean']
        cleaned_data = self.clean_data(imported_data, rename_col=clean_json['Rename Col'], drop_col=clean_json['Drop Col'],
                                        resample=clean_json['Resample'], freq=clean_json['Frequency'], resampler=clean_json['Resampler'],
                                        interpolate=clean_json['Interpolate'], limit=clean_json['Limit'],
                                        method=clean_json['Method'], remove_na=clean_json['Remove NA'],
                                        remove_na_how=clean_json['Remove NA How'], remove_outliers=clean_json['Remove Outliers'],
                                        sd_val=clean_json['SD Val'], remove_out_of_bounds=clean_json['Remove Out of Bounds'],
                                        low_bound=clean_json['Low Bound'], high_bound=clean_json['High Bound'],
                                        save_file=clean_json['Save File'])

        preproc_json = input_json['Preprocess']
        preprocessed_data = self.preprocess_data(cleaned_data, cdh_cpoint=preproc_json['CDH CPoint'],
                                                hdh_cpoint=preproc_json['HDH CPoint'], col_hdh_cdh=preproc_json['HDH CDH Calc Col'],
                                                col_degree=preproc_json['Col Degree'], degree=preproc_json['Degree'],
                                                standardize=preproc_json['Standardize'], normalize=preproc_json['Normalize'],
                                                year=preproc_json['Year'], month=preproc_json['Month'], week=preproc_json['Week'],
                                                tod=preproc_json['Time of Day'], dow=preproc_json['Day of Week'],
                                                save_file=preproc_json['Save File'])

        model_json = input_json['Model']
        model_data = self.model(preprocessed_data, ind_col=model_json['Independent Col'], dep_col=model_json['Dependent Col'],
                                project_ind_col=model_json['Projection Independent Col'],
                                baseline_period=model_json['Baseline Period'], projection_period=model_json['Projection Period'],
                                exclude_time_period=model_json['Exclude Time Period'],
                                alphas=model_json['Alphas'], cv=model_json['CV'], plot=model_json['Plot'], figsize=model_json['Fig Size'])


    # CHECK: Modify looping of time_freq
    def search(self, file_name, imported_data=None):
        """ Run models on different data configurations.

        Note
        ----
        The input json file should include ALL parameters.

        Parameters
        ----------
        file_name       : str
            Optional json file to read parameters.
        imported_data   : pd.DataFrame()
            Pandas Dataframe containing data.

        """

        resample_freq=['15T', 'h', 'd']
        time_freq = {
            'year'  :   [True,  False,  False,  False,  False],
            'month' :   [False, True,   False,  False,  False],
            'week'  :   [False, False,  True,   False,  False],
            'tod'   :   [False, False,  False,  True,   False],
            'dow'   :   [False, False,  False,  False,  True],
        }
        
        optimal_score = float('-inf')
        optimal_model = None

        # CSV Files
        if not imported_data:
            with open(file_name) as f:
                input_json = json.load(f)
                import_json = input_json['Import']
                imported_data = self.import_data(file_name=import_json['File Name'], folder_name=import_json['Folder Name'],
                                                head_row=import_json['Head Row'], index_col=import_json['Index Col'],
                                                convert_col=import_json['Convert Col'], concat_files=import_json['Concat Files'],
                                                save_file=import_json['Save File'])

        with open(file_name) as f:
            input_json = json.load(f)

            for x in resample_freq: # Resample data interval
                input_json['Clean']['Frequency'] = x

                for i in range(len(time_freq.items())): # Add time features
                    input_json['Preprocess']['Year']        = time_freq['year'][i]
                    input_json['Preprocess']['Month']       = time_freq['month'][i]
                    input_json['Preprocess']['Week']        = time_freq['week'][i]
                    input_json['Preprocess']['Time of Day'] = time_freq['tod'][i]
                    input_json['Preprocess']['Day of Week'] = time_freq['dow'][i]

                    # Putting comment in json file to indicate which parameters have been changed
                    time_feature = None
                    for key in time_freq:
                        if time_freq[key][i]:
                            time_feature = key
                    self.result['Comment'] = 'Freq: ' + x + ', ' + 'Time Feature: ' + time_feature

                    # Read parameters in input_json
                    self.read_json(file_name=None, input_json=input_json, imported_data=imported_data)
                    
                    # Keep track of highest adj_r2 score
                    if self.result['Model']['Optimal Model\'s Metrics']['adj_r2'] > optimal_score:
                        optimal_score = self.result['Model']['Optimal Model\'s Metrics']['adj_r2']
                        optimal_model_file_name = self.results_folder_name + '/results-' + str(self.get_global_count()) + '.json'

                    # Wrapper.global_count += 1

        print('Most optimal model: ', optimal_model_file_name)
        freq = self.result['Comment'].split(' ')[1][:-1]
        time_feat = self.result['Comment'].split(' ')[-1]
        print('Freq: ', freq, 'Time Feature: ', time_feat)


    def import_data(self, file_name='*', folder_name='.', head_row=0, index_col=0,
                    convert_col=True, concat_files=False, save_file=True):
        """ Imports csv file(s) and stores the result in self.imported_data.
            
        Note
        ----
        1. If folder exists out of current directory, folder_name should contain correct regex
        2. Assuming there's no file called "\*.csv"

        Parameters
        ----------
        file_name       : str
            CSV file to be imported. Defaults to '\*' - all csv files in the folder.
        folder_name     : str
            Folder where file resides. Defaults to '.' - current directory.
        head_row        : int
            Skips all rows from 0 to head_row-1
        index_col       : int
            Skips all columns from 0 to index_col-1
        convert_col     : bool
            Convert columns to numeric type
        concat_files    : bool
            Appends data from files to result dataframe
        save_file       : bool
            Specifies whether to save file or not. Defaults to True.

        Returns
        -------
        pd.DataFrame()
            Dataframe containing imported data.

        """
        
        # Create instance and import the data
        import_data_obj = Import_Data()
        import_data_obj.import_csv(file_name=file_name, folder_name=folder_name, 
                                head_row=head_row, index_col=index_col, 
                                convert_col=convert_col, concat_files=concat_files)
        
        # Store imported data in wrapper class
        self.imported_data = import_data_obj.data

        # Logging
        self.result['Import'] = {
            'File Name': file_name,
            'Folder Name': folder_name,
            'Head Row': head_row,
            'Index Col': index_col,
            'Convert Col': convert_col,
            'Concat Files': concat_files,
            'Save File': save_file
        }
        
        if save_file:
            f = self.results_folder_name + '/imported_data-' + str(self.get_global_count()) + '.csv'
            self.imported_data.to_csv(f)
            self.result['Import']['Saved File'] = f
        else:
            self.result['Import']['Saved File'] = ''

        return self.imported_data


    def clean_data(self, data, rename_col=None, drop_col=None,
                    resample=True, freq='h', resampler='mean',
                    interpolate=True, limit=1, method='linear',
                    remove_na=True, remove_na_how='any',
                    remove_outliers=True, sd_val=3,
                    remove_out_of_bounds=True, low_bound=0, high_bound=float('inf'),
                    save_file=True):
        """ Cleans dataframe according to user specifications and stores result in self.cleaned_data.

        Parameters
        ----------
        data                    : pd.DataFrame()
            Dataframe to be cleaned.
        rename_col              : list(str)
            List of new column names.
        drop_col                : list(str)
            Columns to be dropped.
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
        save_file       : bool
            Specifies whether to save file or not. Defaults to True.

        Returns
        -------
        pd.DataFrame()
            Dataframe containing cleaned data.

        """

        # Check to ensure data is a pandas dataframe
        if not isinstance(data, pd.DataFrame):
            raise TypeError('data has to be a pandas dataframe.')
        
        # Create instance and clean the data
        clean_data_obj = Clean_Data(data)
        clean_data_obj.clean_data(resample=resample, freq=freq, resampler=resampler,
                                interpolate=interpolate, limit=limit, method=method,
                                remove_na=remove_na, remove_na_how=remove_na_how,
                                remove_outliers=remove_outliers, sd_val=sd_val,
                                remove_out_of_bounds=remove_out_of_bounds, low_bound=low_bound, high_bound=high_bound)

        # Correlation plot
        # fig = self.plot_data_obj.correlation_plot(clean_data_obj.cleaned_data)
        # fig.savefig(self.results_folder_name + '/correlation_plot-' + str(Wrapper.global_count) + '.png')

        if rename_col:  # Rename columns of dataframe
            clean_data_obj.rename_columns(rename_col)
        if drop_col:    # Drop columns of dataframe
            clean_data_obj.drop_columns(drop_col)

        # Store cleaned data in wrapper class
        self.cleaned_data = clean_data_obj.cleaned_data

        # Logging
        self.result['Clean'] = {
            'Rename Col': rename_col,
            'Drop Col': drop_col,
            'Resample': resample,
            'Frequency': freq,
            'Resampler': resampler,
            'Interpolate': interpolate,
            'Limit': limit,
            'Method': method,
            'Remove NA': remove_na,
            'Remove NA How': remove_na_how,
            'Remove Outliers': remove_outliers,
            'SD Val': sd_val,
            'Remove Out of Bounds': remove_out_of_bounds,
            'Low Bound': low_bound,
            'High Bound': str(high_bound) if high_bound == float('inf') else high_bound,
            'Save File': save_file
        }

        if save_file:
            f = self.results_folder_name + '/cleaned_data-' + str(self.get_global_count()) + '.csv'
            self.cleaned_data.to_csv(f)
            self.result['Clean']['Saved File'] = f
        else:
            self.result['Clean']['Saved File'] = ''

        return self.cleaned_data


    def preprocess_data(self, data,
                        hdh_cpoint=65, cdh_cpoint=65, col_hdh_cdh=None,
                        col_degree=None, degree=None,
                        standardize=False, normalize=False,
                        year=False, month=False, week=False, tod=False, dow=False,
                        save_file=True):
        """ Preprocesses dataframe according to user specifications and stores result in self.preprocessed_data.

        Parameters
        ----------
        data            : pd.DataFrame()
            Dataframe to be preprocessed.
        hdh_cpoint      : int
            Heating degree hours. Defaults to 65.
        cdh_cpoint      : int
            Cooling degree hours. Defaults to 65.
        col_hdh_cdh     : str
            Column name which contains the outdoor air temperature.
        col_degree      : list(str)
            Column to exponentiate.
        degree          : list(str)
            Exponentiation degree.
        standardize     : bool
            Standardize data.
        normalize       : bool
            Normalize data.
        year            : bool
            Year.
        month           : bool
            Month.
        week            : bool
            Week.
        tod             : bool
            Time of Day.
        dow             : bool
            Day of Week.
        save_file       : bool
            Specifies whether to save file or not. Defaults to True.

        Returns
        -------
        pd.DataFrame()
            Dataframe containing preprocessed data.

        """

        # Check to ensure data is a pandas dataframe
        if not isinstance(data, pd.DataFrame):
            raise TypeError('data has to be a pandas dataframe.')
        
        # Create instance
        preprocess_data_obj = Preprocess_Data(data)
        if col_hdh_cdh:
            preprocess_data_obj.add_degree_days(col=col_hdh_cdh, hdh_cpoint=hdh_cpoint, cdh_cpoint=cdh_cpoint)
        preprocess_data_obj.add_col_features(col=col_degree, degree=degree)

        if standardize:
            preprocess_data_obj.standardize()
        if normalize:
            preprocess_data_obj.normalize()

        preprocess_data_obj.add_time_features(year=year, month=month, week=week, tod=tod, dow=dow)
        
        # Store preprocessed data in wrapper class
        self.preprocessed_data = preprocess_data_obj.preprocessed_data

        # Logging
        self.result['Preprocess'] = {
            'HDH CPoint': hdh_cpoint,
            'CDH CPoint': cdh_cpoint,
            'HDH CDH Calc Col': col_hdh_cdh,
            'Col Degree': col_degree,
            'Degree': degree,
            'Standardize': standardize,
            'Normalize': normalize,
            'Year': year,
            'Month': month,
            'Week': week,
            'Time of Day': tod,
            'Day of Week': dow,
            'Save File': save_file
        }

        if save_file:
            f = self.results_folder_name + '/preprocessed_data-' + str(self.get_global_count()) + '.csv'
            self.preprocessed_data.to_csv(f)
            self.result['Preprocess']['Saved File'] = f
        else:
            self.result['Preprocess']['Saved File'] = ''

        return self.preprocessed_data


    def model(self, data,
            ind_col=None, dep_col=None,
            project_ind_col=None,
            baseline_period=[None, None], projection_period=None, exclude_time_period=None,
            alphas=np.logspace(-4,1,30),
            cv=3, plot=True, figsize=None,
            custom_model_func=None):
        """ Split data into baseline and projection periods, run models on them and display metrics & plots.

        Parameters
        ----------
        data                    : pd.DataFrame()
            Dataframe to model.
        ind_col                 : list(str)
            Independent column(s) of dataframe. Defaults to all columns except the last.
        dep_col                 : str
            Dependent column of dataframe.
        project_ind_col         : list(str)
            Independent column(s) to use for projection. If none, use ind_col.
        baseline_period         : list(str)
            List of time periods to split the data into baseline periods. It needs to have a start and an end date.
        projection_period       : list(str)
            List of time periods to split the data into projection periods. It needs to have a start and an end date.
        exclude_time_period     : list(str)
            List of time periods to exclude for modeling.
        alphas                  : list(int)
            List of alphas to run regression on.
        cv                      : int
            Number of folds for cross-validation.
        plot                    : bool
            Specifies whether to save plots or not.
        figsize                 : tuple
            Size of the plots.
        custom_model_func       : function
            Model with specific hyper-parameters provided by user.

        Returns
        -------
        dict
            Metrics of the optimal/best model.

        """

        # Check to ensure data is a pandas dataframe
        if not isinstance(data, pd.DataFrame):
            raise TypeError('data has to be a pandas dataframe.')
        
        # Create instance
        model_data_obj = Model_Data(data, ind_col, dep_col, alphas, cv, exclude_time_period, baseline_period, projection_period)

        # Split data into baseline and projection
        model_data_obj.split_data()

        # Logging
        self.result['Model'] = {
            'Independent Col': ind_col,
            'Dependent Col': dep_col,
            'Projection Independent Col': project_ind_col,
            'Baseline Period': baseline_period,
            'Projection Period': projection_period,
            'Exclude Time Period': exclude_time_period,
            'Alphas': list(alphas),
            'CV': cv,
            'Plot': plot,
            'Fig Size': figsize
        }

        # Runs all models on the data and returns optimal model
        all_metrics = model_data_obj.run_models()
        self.result['Model']['All Model\'s Metrics'] = all_metrics

        # CHECK: Define custom model's parameter and return types in documentation.
        if custom_model_func:
            self.result['Model']['Custom Model\'s Metrics'] = model_data_obj.custom_model(custom_model_func)

        # Fit optimal model to data
        self.result['Model']['Optimal Model\'s Metrics'] = model_data_obj.best_model_fit()

        if plot:

            # Use project_ind_col if projecting into the future (no input data other than weather data)
            input_col = model_data_obj.input_col if not project_ind_col else project_ind_col
            fig, y_true, y_pred = self.plot_data_obj.baseline_projection_plot(model_data_obj.y_true, model_data_obj.y_pred, 
                                                            model_data_obj.baseline_period, model_data_obj.projection_period,
                                                            model_data_obj.best_model_name, model_data_obj.best_metrics['adj_r2'],
                                                            model_data_obj.original_data,
                                                            input_col, model_data_obj.output_col,
                                                            model_data_obj.best_model,
                                                            self.result['Site'])

            fig.savefig(self.results_folder_name + '/baseline_projection_plot-' + str(self.get_global_count()) + '.png')
            
            if not y_true.empty and not y_pred.empty:
                saving_absolute = (y_pred - y_true).sum()
                saving_perc = (saving_absolute / y_pred.sum()) * 100
                self.result['Energy Savings (%)'] = float(saving_perc)
                self.result['Energy Savings (absolute)'] = saving_absolute

                # Temporary
                self.project_df['true'] = y_true
                self.project_df['pred'] = y_pred

                # Calculate uncertainity of savings
                self.result['Uncertainity'] = self.uncertainity_equation(model_data_obj, y_true, y_pred, 0.9)
            
            else:
                print('y_true: ', y_true)
                print('y_pred: ', y_pred)
                print('Error: y_true and y_pred are empty. Default to -1.0 savings.')
                self.result['Energy Savings (%)'] = float(-1.0)
                self.result['Energy Savings (absolute)'] = float(-1.0)
        
        return self.best_metrics


    def uncertainity_equation(self, model_data_obj, E_measured, E_predicted, confidence_level):
        """
        model_data_obj      : Model_Data()
            An instance of Model_Data() which is a user defined class.
        E_measured          : pd.Series()
            Actual values of energy in the post-retrofit period.
        E_predicted         : pd.Series()
            Predicted values of energy in the post-retrofit period.
        confidence_level    : float
            Confidence level of uncertainity in decimal, i.e. 90% = 0.9

        """
        
        # Number of rows in baseline period
        n = model_data_obj.baseline_in.shape[0]

        # Number of columns in baseline period
        p = model_data_obj.baseline_in.shape[1]
        
        # Number of rows in post period
        m = E_measured.count()
        
        # t-stats value
        # CHECK: degrees of freedom = E_predicted.count() - 1?
        t = stats.t.ppf(confidence_level, E_predicted.count() - 1)

        # Rho - Autocorrelation coefficient
        residuals = E_measured - E_predicted 
        auto_corr = residuals.autocorr(lag=1)
        rho = pow(auto_corr, 0.5)

        # Effective number of points after accounting for autocorrelation
        n_prime = n * ((1 - rho) / (1 + rho))
        
        # Coefficient of variation of RMSE
        # CHECK: Is the denominator correct?
        cv_rmse = pow(sum(pow(E_measured - E_predicted, 2) / (n - p)), 0.5) / (sum(E_measured) / E_measured.count())
        
        # Bracket in the numerator - refer to page 20
        numerator_bracket = pow((n / n_prime) * (1 + (2 / n_prime)) * (1 / m), 0.5)
        
        # Esave should be absolute value? 
        f = abs(sum(E_measured - E_predicted) / sum(model_data_obj.y_true))
           
        # Main equation 
        uncertainity = t * ((1.26 * cv_rmse * numerator_bracket) / f)
        
        return uncertainity
