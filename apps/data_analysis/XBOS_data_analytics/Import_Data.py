""" This script imports data from csv files and returns a dataframe. 

Note
----
1. CSV - If only folder is specified and no filename, all csv's will be read in sorted order by name. \n
2. CSV - Doesn't handle cases when user provides \n
    \t 1. file_name of type str and folder_name of type list(str) \n
    \t 2. file_name and folder_name both of type list(str)

To Do \n
    \t 1. Remove Import_XBOS from Import_Data.

Authors \n
@author Marco Pritoni <marco.pritoni@gmail.com> \n
@author Jacob Rodriguez  <jbrodriguez@ucdavis.edu> \n
@author Pranav Gupta <phgupta@ucdavis.edu> \n

Last modified: November 12 2018 \n

"""

import os
import glob
import numpy as np
import pandas as pd


class Import_Data:

    """ This class imports data from csv files """

    def __init__(self):
        """ Constructor.

        This class stores the imported data.

        """
        self.data = pd.DataFrame()


    def import_csv(self, file_name='*', folder_name='.', head_row=0, index_col=0, convert_col=True, concat_files=False):
        """ Imports csv file(s) and stores the result in data.
            
        Note
        ----
        1. If folder exists out of current directory, folder_name should contain correct regex
        2. Assuming there's no file called "\*.csv"

        Parameters
        ----------
        file_name       : str
            CSV file to be imported. Defaults to '\*', i.e. all csv files in the folder.
        folder_name     : str
            Folder where file resides. Defaults to '.', i.e. current directory.
        head_row        : int
            Skips all rows from 0 to head_row-1
        index_col       : int
            Skips all columns from 0 to index_col-1
        convert_col     : bool
            Convert columns to numeric type
        concat_files    : bool
            Appends data from files to result dataframe

        """

        # Import a specific or all csv files in folder
        if isinstance(file_name, str) and isinstance(folder_name, str):
            try:
                self.data = self._load_csv(file_name, folder_name, head_row, index_col, convert_col, concat_files)
            except Exception as e:
                raise e

        # Import multiple csv files in a particular folder.
        elif isinstance(file_name, list) and isinstance(folder_name, str):

            for i, file in enumerate(file_name):
                if isinstance(head_row, list):
                    _head_row = head_row[i]
                else:
                    _head_row = head_row

                if isinstance(index_col, list):
                    _index_col = index_col[i]
                else:
                    _index_col = index_col

                try:
                    data_tmp = self._load_csv(file, folder_name, _head_row, _index_col, convert_col, concat_files)
                    if concat_files:
                        self.data = self.data.append(data_tmp, ignore_index=False, verify_integrity=False)
                    else:
                        self.data = self.data.join(data_tmp, how="outer")
                except Exception as e:
                    raise e

        else:
            # Current implementation can't accept,
            # 1. file_name of type str and folder_name of type list(str)
            # 2. file_name and folder_name both of type list(str)
            raise NotImplementedError("Filename and Folder name can't both be of type list.")


    def _load_csv(self, file_name, folder_name, head_row, index_col, convert_col, concat_files):
        """ Load single csv file.

        Parameters
        ----------
        file_name       : str
            CSV file to be imported. Defaults to '*' - all csv files in the folder.
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

        Returns
        -------
        pd.DataFrame()
            Dataframe containing csv data

        """

        # Denotes all csv files
        if file_name == "*":

            if not os.path.isdir(folder_name):
                raise OSError('Folder does not exist.')
            else:
                file_name_list = sorted(glob.glob(folder_name + '*.csv'))

                if not file_name_list:
                    raise OSError('Either the folder does not contain any csv files or invalid folder provided.')
                else:
                    # Call previous function again with parameters changed (file_name=file_name_list, folder_name=None)
                    # Done to reduce redundancy of code
                    self.import_csv(file_name=file_name_list, head_row=head_row, index_col=index_col,
                                    convert_col=convert_col, concat_files=concat_files)
                    return self.data

        else:
            if not os.path.isdir(folder_name):
                raise OSError('Folder does not exist.')
            else:
                path = os.path.join(folder_name, file_name)

                if head_row > 0:
                    data = pd.read_csv(path, index_col=index_col, skiprows=[i for i in range(head_row-1)])
                else:
                    data = pd.read_csv(path, index_col=index_col)

                # Convert time into datetime format
                try:
                    # Special case format 1/4/14 21:30
                    data.index = pd.to_datetime(data.index, format='%m/%d/%y %H:%M')
                except:
                    data.index = pd.to_datetime(data.index, dayfirst=False, infer_datetime_format=True)

        # Convert all columns to numeric type
        if convert_col:
            # Check columns in dataframe to see if they are numeric
            for col in data.columns:
                # If particular column is not numeric, then convert to numeric type
                if data[col].dtype != np.number:
                    data[col] = pd.to_numeric(data[col], errors="coerce")

        return data


class Import_XBOS(Import_Data):

    """ This class imports data from XBOS """

    def __init__(self):
        """ Constructor.

        This class imports the dataclient module & stores the imported data.

        """

        import dataclient
        self.weather_data = pd.DataFrame()
        self.power_data = pd.DataFrame()
        self.temp_data = pd.DataFrame()
        self.hsp_data = pd.DataFrame()
        self.csp_data = pd.DataFrame()


    def get_weather_power_tstat(self, site, start, end, data_type=['weather', 'power']):
        """ Get weather and power data.

        Parameters
        ----------
        site        : str
            Site name.
        start       : str
            Start date.
        end         : str
            End date.
        data_type   : str
            Type of data needed (all, weather, power, temperature, hsp, csp)

        """

        m = dataclient.MDALClient("corbusier.cs.berkeley.edu:8088")

        request = {
            "Variables": {
                "greenbutton": {
                    "Definition": """SELECT ?meter ?meter_uuid FROM %s WHERE {
                        ?meter rdf:type brick:Green_Button_Meter .
                        ?meter bf:uuid ?meter_uuid
                    };""" % site,
                },
                "weather": {
                    "Definition": """SELECT ?t ?t_uuid FROM %s WHERE {
                        ?t rdf:type/rdfs:subClassOf* brick:Weather_Temperature_Sensor .
                        ?t bf:uuid ?t_uuid
                    };""" % site,
                },
                "tstat_state": {
                    "Definition": """SELECT ?t ?t_uuid ?tstat FROM %s WHERE {
                        ?t rdf:type/rdfs:subClassOf* brick:Thermostat_Status .
                        ?t bf:uuid ?t_uuid
                        ?t bf:isPointOf ?tstat .
                        ?tstat rdf:type brick:Thermostat
                    };""" % site,
                },
                "tstat_hsp": {
                    "Definition": """SELECT ?t ?t_uuid ?tstat FROM %s WHERE {
                        ?t rdf:type/rdfs:subClassOf* brick:Supply_Air_Temperature_Heating_Setpoint .
                        ?t bf:uuid ?t_uuid .
                        ?t bf:isPointOf ?tstat .
                        ?tstat rdf:type brick:Thermostat
                    };""" % site,
                },
                "tstat_csp": {
                    "Definition": """SELECT ?t ?t_uuid ?tstat FROM %s WHERE {
                        ?t rdf:type/rdfs:subClassOf* brick:Supply_Air_Temperature_Cooling_Setpoint .
                        ?t bf:uuid ?t_uuid .
                        ?t bf:isPointOf ?tstat .
                        ?tstat rdf:type brick:Thermostat
                    };""" % site,
                },
                "tstat_temp": {
                    "Definition": """SELECT ?t ?t_uuid ?tstat FROM %s WHERE {
                        ?t rdf:type/rdfs:subClassOf* brick:Temperature_Sensor .
                        ?t bf:uuid ?t_uuid .
                        ?t bf:isPointOf ?tstat .
                        ?tstat rdf:type brick:Thermostat
                    };""" % site,
                },
            },
        }

        # outside air temp
        request['Composition'] = ['weather']
        request['Aggregation'] = {'weather': ['MEAN']}
        request['Time'] = {
            'Start': start,
            'End': end,
            'Window': '15m',
            'Aligned': True
        }
        resp_weather = m.query(request)
        self.weather_data = resp_weather.df

        # power
        request['Composition'] = ['greenbutton']
        request['Aggregation'] = {'greenbutton': ['MEAN']}
        resp_power = m.query(request)
        self.power_data = resp_power.df

        # tstat temperature
        request['Composition'] = ['tstat_temp', 'tstat_hsp', 'tstat_csp']
        request['Aggregation'] = {'tstat_temp': ['MEAN']}
        resp_temp  = m.query(request)
        self.temp_data = resp_temp

        # tstat heat setpoint
        request['Composition'] = ['tstat_hsp']
        request['Aggregation'] = {'tstat_hsp': ['MAX']}
        resp_hsp = m.query(request)
        self.hsp_data = resp_hsp

        # tstat cool setpoint
        request['Composition'] = ['tstat_csp']
        request['Aggregation'] = {'tstat_csp': ['MAX']}
        resp_csp = m.query(request)
        self.csp_data = resp_csp

        mapping = {
            'weather': resp_weather,
            'power': resp_power,
            'temperature': resp_temp, 
            'hsp': resp_hsp,
            'csp': resp_csp
        }

        first = True
        for dat in data_type:
            if first:
                try:
                    self.data = mapping[dat].df
                    first = False
                except:
                    raise SystemError('Undefined data_type (Make sure all characters are lowercase)')
            else:
                try:
                    self.data = self.data.join(mapping[dat].df)
                except:
                    raise SystemError('Undefined data_type (Make sure all characters are lowercase)')

        return mapping


class Import_MDAL(Import_Data):

    def __init__(self):

        import dataclient
        self.m = dataclient.MDALClient("corbusier.cs.berkeley.edu:8088")


    def get_meter(self, site, start, end, var="meter", agg='MEAN', window='24h', aligned=True, return_names=True):
    
        point_type = 'Green_Button_Meter'
        request = self.compose_MDAL_dic(point_type=point_type, site=site, start=start, end=end,  var=var, agg=agg, window=window, aligned=aligned)
        resp = self.m.query(request)
        
        if return_names:
            resp = self.replace_uuid_w_names(resp)
        
        return resp

    def get_weather(self, site, start, end,  var="weather", agg='MEAN', window='24h', aligned=True, return_names=True):

        point_type = 'Weather_Temperature_Sensor'
        request = self.compose_MDAL_dic(point_type=point_type, site=site, start=start, end=end,  var=var, agg=agg, window=window, aligned=aligned)
        resp = self.m.query(request)

        if return_names:
            resp = self.replace_uuid_w_names(resp)

        return resp

    def get_tstat(self, site, start, end,  var="tstat_temp", agg='MEAN', window='24h', aligned=True, return_names=True):
    
        point_map = {"tstat_state" : "Thermostat_Status", 
                     "tstat_hsp" : "Supply_Air_Temperature_Heating_Setpoint", 
                     "tstat_csp" : "Supply_Air_Temperature_Cooling_Setpoint", 
                     "tstat_temp": "Temperature_Sensor" } 
        
        if isinstance(var,list):
            point_type = [point_map[point_type] for point_type in var] # list of all the point names using BRICK classes
        else:
            point_type = point_map[var] # single value using BRICK classes
        
        request = self.compose_MDAL_dic(point_type=point_type, site=site, start=start, end=end,  var=var, agg=agg, window=window, aligned=aligned)
        resp = self.m.query(request)
        
        if return_names:
            resp = self.replace_uuid_w_names(resp)

        return resp


    def compose_MDAL_dic(self, point_type, site, start, end,  var, agg, window, aligned, points=None, return_names=False):
    
        request = {} 
        # add Time Details - single set for one or multiple series
        request['Time'] = {
            'Start': start,
            'End': end,
            'Window': window,
            'Aligned': aligned
                           }
        # define Variables 
        request["Variables"] = {}
        request['Composition'] = []
        request['Aggregation'] = {}
        
        if isinstance(point_type, str): # if point_type is a string -> single type of point requested
            request["Variables"][var] =  self.compose_BRICK_query(point_type=point_type,site=site) # pass one point type at the time
            request['Composition'] = [var]
            request['Aggregation'][var] = [agg]
            
        elif isinstance(point_type, list): # loop through all the point_types and create one section of the brick query at the time

            for idx, point in enumerate(point_type): 
                request["Variables"][var[idx]] =  self.compose_BRICK_query(point_type=point,site=site) # pass one point type at the time
                request['Composition'].append(var[idx])
                
                if isinstance(agg, str): # if agg is a string -> single type of aggregation requested
                    request['Aggregation'][var[idx]] = [agg]
                elif isinstance(agg, list): # if agg is a list -> expected one agg per point
                    request['Aggregation'][var[idx]] = [agg[idx]]
        
        #pprint.pprint(request)
        return request

    def compose_BRICK_query(self, point_type,site):
    
    
        if point_type == "Green_Button_Meter":
            BRICK_query = {"Definition": """SELECT ?point ?uuid FROM %s WHERE {
                                                        ?point rdf:type brick:%s .
                                                        ?point bf:uuid ?uuid                
                                                                              };""" % (site,point_type)
                          }
        if point_type == "Weather_Temperature_Sensor":
            BRICK_query = {"Definition": """SELECT ?point ?uuid FROM %s WHERE {
                                                   ?point rdf:type/rdfs:subClassOf* brick:%s .
                                                   ?point bf:uuid ?uuid
                                                                            };""" % (site,point_type)
                          }
            
        if point_type in ["Thermostat_Status","Supply_Air_Temperature_Heating_Setpoint",
                          "Supply_Air_Temperature_Cooling_Setpoint","Temperature_Sensor"]: ##  "tstat_state","tstat_hsp","tstat_csp","tstat_temp": 
            BRICK_query = {"Definition": """SELECT ?point ?uuid ?equip FROM %s WHERE {
                                            ?point rdf:type/rdfs:subClassOf* brick:%s .
                                            ?point bf:uuid ?uuid .
                                            ?point bf:isPointOf ?equip .
                                            ?equip rdf:type brick:Thermostat };""" % (site,point_type)
                          }
        
        return BRICK_query

    def parse_context(self, context):
    
        metadata_table = pd.DataFrame(context).T

        return metadata_table

    def strip_point_name(self, col):
    
        return col.str.split("#",expand=True)[1]

    def get_point_name(self, context):
    
        metadata_table = self.parse_context(context)
    
        return metadata_table.apply(self.strip_point_name, axis=1)

    def replace_uuid_w_names(self, resp):
        col_mapper = self.get_point_name(resp.context)["?point"].to_dict()
        resp.df.rename(columns = col_mapper, inplace=True)
        return resp
