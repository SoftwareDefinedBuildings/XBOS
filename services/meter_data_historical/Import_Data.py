""" This script gets meter data from pymortar. """

import pymortar
from datetime import datetime
from pytz import timezone
from collections import defaultdict


class Import_Data():

    """ This class queries data from pymortar.

    Note
    ----
    For pymortar, set the evironment variables - $MORTAR_API_USERNAME & $MORTAR_API_PASSWORD.

    For Mac,
    1. vi ~/.bash_profile
    2. At the end of file add,
        1. export $MORTAR_API_USERNAME=username
        2. export $MORTAR_API_PASSWORD=password
    3. source ~/.bash_profile

    """

    def __init__(self):
        """ Constructor: Create pymortar client. """

        self.client = pymortar.Client({})

    @staticmethod
    def convert_to_utc(time):
        """ Convert time to UTC

        Parameters
        ----------
        time    : str
            Time to convert. Has to be of the format '2016-01-01T00:00:00-08:00'.

        Returns
        -------
        str
            UTC timestamp.

        """

        # time is already in UTC
        if 'Z' in time:
            return time
        else:
            time_formatted = time[:-3] + time[-2:]
            dt = datetime.strptime(time_formatted, '%Y-%m-%dT%H:%M:%S%z')
            dt = dt.astimezone(timezone('UTC'))
            return dt.strftime('%Y-%m-%dT%H:%M:%SZ')

    def get_meter_data(self, site, start, end, point_type="Green_Button_Meter", agg='MEAN', window='15m'):
        """ Get meter data from Mortar.

        Parameters
        ----------
        site            : list(str)
            List of sites.
        start           : str
            Start date - 'YYYY-MM-DDTHH:MM:SSZ'
        end             : str
            End date - 'YYYY-MM-DDTHH:MM:SSZ'
        point_type      : str
            Type of data, i.e. Green_Button_Meter, Building_Electric_Meter...
        agg             : str
            Values include MEAN, MAX, MIN, COUNT, SUM and RAW (the temporal window parameter is ignored)
        window          : str
            Size of the moving window.
        
        Returns
        -------
        pd.DataFrame(), defaultdict(list)
            Meter data, dictionary that maps meter data's columns (uuid's) to sitenames.

        """

        # In case user enter 'mean' instead of 'MEAN'
        agg = agg.upper()

        switcher = {
            'MEAN': pymortar.MEAN,
            'MAX': pymortar.MAX,
            'MIN': pymortar.MIN,
            'COUNT': pymortar.COUNT,
            'SUM': pymortar.SUM,
            'RAW': pymortar.RAW
        }

        agg = switcher.get(agg)

        # Convert time to UTC
        start = self.convert_to_utc(start)
        end = self.convert_to_utc(end)

        query_meter = "SELECT ?meter WHERE { ?meter rdf:type brick:" + point_type + " };"

        # Define the view of meters (metadata)
        meter = pymortar.View(
            name="view_meter",
            sites=site,
            definition=query_meter
        )

        # Define the meter timeseries stream
        data_view_meter = pymortar.DataFrame(
            name="data_meter", # dataframe column name
            aggregation=agg,
            window=window,
            timeseries=[
                pymortar.Timeseries(
                    view="view_meter",
                    dataVars=["?meter"]
                )
            ]
        )

        # Define timeframe
        time_params = pymortar.TimeParams(
            start=start,
            end=end
        )

        # Form the full request object
        request = pymortar.FetchRequest(
            sites=site,
            views=[meter],
            dataFrames=[data_view_meter],
            time=time_params
        )

        # Fetch data from request
        response = self.client.fetch(request)

        # resp_meter = (url, uuid, sitename)
        resp_meter = response.query('select * from view_meter')

        # Map's uuid's to the site names
        map_uuid_sitename = defaultdict(list)
        for (url, uuid, sitename) in resp_meter:
            map_uuid_sitename[uuid].append(sitename)

        return response['data_meter'], map_uuid_sitename
