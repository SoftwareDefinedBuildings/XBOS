__author__ = 'Olivier Van Cutsem'

from .rate_structure import *
from .tariff_structure import TariffType
from dateutil.relativedelta import relativedelta
import pandas as pd
import pytz


class CostCalculator(object):
    """
    This class is used to manipulate the building electricity cost:
        - Bill calculation given a Smart Meter power timeseries
        - Electricity price timeseries between two dates
        - Cost coefficients over a given period, for a linear optimization problem
        - Metrics related to the tariff maximum demand

    The main component of this class is called the "tariff_structure".
    It is a dictionnary that lists electricity cost information for each type (fix, energy or demand).
    The list for each type of billing stores "blocks" of data, that collect data about the tariffication of the electricity for a specific PERIOD of time.
    Any time a new tariffication (e.g. a PDP event, or a new base tariff) must be added for a new time period, one just need to add the "block" of data in the corresponding list.

    """

    # This default structure lists the tariffs type for most of the utilities in US
    DEFAULT_TARIFF_MAP = {str(TariffType.FIX_CUSTOM_CHARGE.value): ChargeType.FIXED,
                          str(TariffType.ENERGY_CUSTOM_CHARGE.value): ChargeType.ENERGY,
                          str(TariffType.DEMAND_CUSTOM_CHARGE_SEASON.value): ChargeType.DEMAND,
                          str(TariffType.DEMAND_CUSTOM_CHARGE_TOU.value): ChargeType.DEMAND,
                          str(TariffType.PDP_ENERGY_CHARGE.value): ChargeType.ENERGY,
                          str(TariffType.PDP_ENERGY_CREDIT.value): ChargeType.ENERGY,
                          str(TariffType.PDP_DEMAND_CREDIT.value): ChargeType.DEMAND,
                          }

    def __init__(self, type_tariffs_map=None):
        """
        Initialize the class instance

        :param type_tariffs_map: [optional] a dictionary that map the main type of tariffs used to describe the whole
        billing logic to their type. DEFAULT_TARIFF_TYPE_LIST is used if type_tariffs_list is not specified.

        Note: the method 'add_tariff' is used to build the core "tariff_structure" object structure.
        """

        # This is the main structure, listing all the "tariff blocks" making up the whole tariff logic
        self.__tariffstructures = {}

        if type_tariffs_map is None:  # The "basic" tariff types as the default ones
            self.type_tariffs_map = self.DEFAULT_TARIFF_MAP
        else:
            self.type_tariffs_map = type_tariffs_map

        # Initialize the list of "tariff blocks"
        for label, type_tariff in list(self.type_tariffs_map.items()):
            self.__tariffstructures[label] = self.generate_type_tariff(type_tariff)

        # Useful data about the tariff
        self.tariff_min_kw = 0  # The minimum peak demand to stay in this tariff
        self.tariff_max_kw = float('inf')  # The maximum peak demand to stay in this tariff

        self.tariff_min_kwh = 0  # The minimum energy demand to stay in this tariff
        self.tariff_max_kwh = float('inf')  # The maximum energy demand to stay in this tariff

    # --- Useful methods

    def compute_bill(self, df, column_data=None, monthly_detailed=False):
        """
        #TODO: create a class for the bill !

        Return the bill corresponding to the electricity data in a data frame:

        {
            "label1": cost_detail_1
            "label2": cost_detail_2
            ...
        }

        where:
         - keys label_i corresponds to a type of tariff in the Enum TariffType and the values
         - values cost_detail_i has one of the following form:
            - if ENERGY or FIX tariff: cost_detail_i = (metric, cost) where metric is either the total energy or the period
            - if DEMAND: cost_detail_i is dict where the keys are the price per kW and the values are tuples: (period-mask, max-power-value, max-power-date)

        if monthly_detailed is set to True, the bill is detailed for each month:

        {
            "YY-MM":
            {
                "label1": (int or float, float) or a dict,    -> the metric associated to the label1 and the corresponding cost (in $) in the month
                "label2": (int or float, float) or a dict,    -> the metric associated to the label2 and the corresponding cost (in $) in the month
                ...
            }
        }

        :param df: a pandas dataframe containing power consumption (in W) in the column 'column_data'.
        If column data is None, it is assumed that only 1 column makes up the df
        :param column_data: [optional] the label of the column containing the power consumption values
        :param monthly_detailed: [optional] if False, it is assumed that the df contains values for ONE billing period.
        if True, the bill is detailed for each month of the calendar. Set to False by default.
        :return: a dictionary representing the bill as described above
        """

        ret = {}

        # Initialize the returned structure

        t_s = df.index[0]
        t_i = datetime(year=t_s.year, month=t_s.month, day=1, tzinfo=t_s.tzinfo)
        while t_i <= df.index[-1]:
            ret[t_i.strftime("%Y-%m")] = {}
            for k in list(self.__tariffstructures.keys()):
                if self.type_tariffs_map[k] == ChargeType.DEMAND:
                    ret[t_i.strftime("%Y-%m")][k] = {}  # a dict of price -> (max, cost)
                else:
                    ret[t_i.strftime("%Y-%m")][k] = (0, 0)  # a tuple

            t_i += relativedelta(months=+1)

        # Compute the bill for each of the tariff type, for each month
        for label, tariff_data in list(self.__tariffstructures.items()):
            l_blocks = self.get_tariff_struct(label, (df.index[0], df.index[-1]))  # get all the tariff blocks for this period and this tariff type
            for tariff_block in l_blocks:
                tariff_cost_list = tariff_block.compute_bill(df, column_data)  # this returns a dict of time-period pointing to tuple that contains both the metric of the bill and the cost
                for time_label, bill_data in list(tariff_cost_list.items()):
                    self.update_bill_structure(ret[time_label], label, bill_data)

        if monthly_detailed is False:  # Aggregate all the months
            return self.aggregate_monthly_bill(ret)
        else:
            return ret

    def get_electricity_price(self, range_date, timestep):
        """

        This function creates the electricity price signal for the specified time frame 'range_date', sampled at 'timestep'
        period. It returns a pandas dataframes where the columns point to each type of tariff, specified in the argument
        'type_tariffs_map' of the constructor.

        :param range_date: a tuple (t_start, t_end) of type 'datetime', representing the period
        :param timestep: an element of TariffElemPeriod enumeration (1h, 30min or 15min), representing the sampling
        period

        :return: a tuple (pd_prices, map_prices) containing:
            - pd_prices: a pandas dataframe whose index is a datetime index and containing as many cols as there are
        type_tariffs_map elements, i.e. the same keys as in __tariffstructures
            - map_prices: a mapping between the cols label and the type of tariff (fix, energy or demand), being of type 'ChargeType'
        """

        # Prepare the Pandas dataframe
        (start_date_price, end_date_price) = range_date
        date_list = pd.date_range(start=start_date_price, end=end_date_price, freq=str(timestep.value))

        # Populate the dataframe for each label, for each period
        ret_df = None
        for label_tariff in list(self.__tariffstructures.keys()):

            if self.type_tariffs_map[label_tariff] == ChargeType.FIXED:  # fixed charges not in the elec price signal
                continue

            df_for_label = self.get_price_in_range(label_tariff, range_date, timestep)

            if ret_df is None:
                ret_df = df_for_label
            else:
                ret_df = pd.concat([ret_df, df_for_label], axis=1)

        return ret_df, self.type_tariffs_map

    def get_price_in_range(self, label_tariff, date_range, timestep):
        """
        Generate a dataframe of the price of
        remark: doesn't work with timestep > 1h ..
        """

        # Prepare the Pandas dataframe
        (start_date_price, end_date_price) = date_range
        date_range = pd.date_range(start=start_date_price, end=end_date_price, freq=str(timestep.value))
        ret_df = pd.DataFrame(index=date_range, columns=[label_tariff])

        # # Select the corresponding blocks for each day and generate the time dataframe
        for idx_day, df_day in ret_df.groupby(ret_df.index.date):
            date_range_period = pd.date_range(start=df_day.index[0], periods=2, freq=str(timestep.value))
            tariff_block = self.get_tariff_struct(label_tariff, (date_range_period[0], date_range_period[1]))

            if len(tariff_block) > 0:
                daily_rate = tariff_block[0].rate_schedule.get_daily_rate(df_day.index[0])
                rate_df = tariff_block[0].get_daily_price_dataframe(daily_rate, df_day)
                ret_df.loc[df_day.index[:], label_tariff] = rate_df['price'].values

        return ret_df

    def print_aggregated_bill(self, bill_struct, verbose=True):
        """
        This method helps manipulating the bill returned by compute_bill().
        It takes the bill as an argument and return a tuple (t, tt, ttt):
         - t is the total cost
         - tt is the total cost per type of tariff (energy, fix, demand)
         - ttt is the cost for each tariff label

        :param bill_struct: the dictionary returned by compute_bill()
        :param verbose: [optional, default is True] print details
        :return:
        """

        monthly_detailed = False

        # If the first keys of the dict point to smth that is not the tariff type, this is a monthly bill
        first_keys_bill_struct = list(bill_struct.keys())
        if first_keys_bill_struct[0] not in list(self.__tariffstructures.keys()):
            monthly_detailed = True

        if monthly_detailed is True:  # This supposes the bill is calculated per natural month of the calendar

            # Aggregation of all the months

            acc_tot = 0.0
            acc_per_chargetype = {ChargeType.FIXED: 0.0, ChargeType.ENERGY: 0.0, ChargeType.DEMAND: 0.0}
            acc_per_label = {}
            for k in list(self.type_tariffs_map.keys()):
                acc_per_label[k] = 0.0

            for m_key, bill_per_label in list(bill_struct.items()):
                for lab_tariff, data in list(bill_per_label.items()):
                    acc_tot += data[1]  # second item in data is in dollar
                    acc_per_chargetype[self.type_tariffs_map[lab_tariff]] += data[1]
                    acc_per_label[lab_tariff] += data[1]
        else:

            # The bill is already aggregated for all the months

            acc_tot = 0.0
            acc_per_chargetype = {ChargeType.FIXED: 0.0, ChargeType.ENERGY: 0.0, ChargeType.DEMAND: 0.0}

            for lab_tariff, data in list(bill_struct.items()):
                if self.type_tariffs_map[lab_tariff] is not ChargeType.DEMAND:
                    cost_per_tariff = data[1]
                else:
                    cost_per_tariff = 0.0
                    for p, data_demand in list(data.items()):
                        cost_per_tariff += p * data_demand['max-demand']

                acc_tot += cost_per_tariff  # second item in data is in dollar
                acc_per_chargetype[self.type_tariffs_map[lab_tariff]] += cost_per_tariff

            acc_per_label = bill_struct

        if verbose:
            # Total
            print(("\n| Aggregated bill: {0} ($)".format(acc_tot)))

            # Per type
            print("\n| Total bill per type of charge:")
            for t_key, v in list(acc_per_chargetype.items()):
                print((" - Charge type '{0}': {1} ($)".format(str(t_key.value), v)))

            # Per label
            print("\n| Total bill per type or tariff:")
            for l_key, v in list(acc_per_label.items()):
                # TODO: print nicely the details ...
                print((" - Type '{0}': {1} ($)".format(str(l_key), v)))

        return acc_tot, acc_per_chargetype, acc_per_label

    # --- Construction and internal methods

    def add_tariff(self, tariff_obj, tariff_label, tariff_type=None):
        """
        Add a tariff block structure that fell into the category "type_rate"
        :param tariff_obj: a TariffBase (or children) object
        :param tariff_label: the label of the tariff, in the keys given to the constructor
        :param tariff_type: the type of tariff, an enum of ChargeType
        :return: /
        """

        # The tariff type (fix, demand or energy) is not specified: get it from the default structure
        if tariff_type is None:
            tariff_type = tariff_label

            if tariff_label in list(self.DEFAULT_TARIFF_MAP.keys()):
                tariff_type = self.DEFAULT_TARIFF_MAP[tariff_label]
            else:
                print("[in add_tariff] Couldn't add the tariff object:" \
                      "The tariff_type is missing and couldn't be retrieved from the label '{0}'".format(tariff_label))  # debug
                return

        # The label tariff is a new one:
        if tariff_label not in list(self.__tariffstructures.keys()):
            self.__tariffstructures[tariff_label] = self.generate_type_tariff(tariff_type)

        self.__tariffstructures[tariff_label]['list_blocks'].append(tariff_obj)

    def get_tariff_struct(self, label_tariff, dates=None):
        """
        Get the list of "tariff blocks" that influence the bill for the type of tariff "type_rate".
        If "dates" is specified, only the blocks that are effective for that period are returned
        :param label_tariff: a string pointing to the type of tariff
        :param dates:[optional] a tuple of type datetime defining the period of selection
        :return: a list of TariffBase (or children) describing the tariffs
        """

        list_struct = self.__tariffstructures[label_tariff]['list_blocks']

        if dates is None:
            return list_struct
        else:
            (start_sel, end_sel) = dates
            if start_sel.tzinfo is None and len(list_struct) > 0:
                first_block = list_struct[0]
                start_sel = start_sel.replace(tzinfo=pytz.timezone('UTC'))

            if end_sel.tzinfo is None and len(list_struct) > 0:
                first_block = list_struct[0]
                end_sel = end_sel.replace(tzinfo=pytz.timezone('UTC'))
                
            return [obj for obj in list_struct if ((obj.startdate <= start_sel <= obj.enddate) or (start_sel <= obj.startdate <= end_sel))]

    def update_bill_structure(self, intermediate_monthly_bill, label_tariff, new_data):
        """
        This method update the current monthly bill with new data for the same month:
         - In case of "demand charge per (k)W", apply MAX
         - In case of "energy charge per (k)Wh or fixed cost per month", apply SUM
        :param intermediate_monthly_bill: the dict structure as return by the compute_bill() method, for a specific month key
        :param label_tariff: a string indicating the tariff. Must be a key of self.__tariffstructures
        :param new_data: a tuple (metric, cost) where:
         - metric is either a float or an int, referring to the metric that influences the cost
         - cost is a float, referring to the cost in $
        :return:
        """

        type_of_tariff = self.__tariffstructures[label_tariff]['type']

        if type_of_tariff == ChargeType.DEMAND:  # Demand: apply MAX
            for p in list(new_data.keys()):  # For each price -> dict (mask, max-p, date-max-p)

                this_mask = new_data[p]['mask']  # get the new data mask
                existing_mask_price = [k for k, v in list(intermediate_monthly_bill[label_tariff].items())  if v['mask'] == this_mask]

                if len(existing_mask_price) > 0:  # this mask has already been seen: APPLY MAX
                    existing_mask_price = existing_mask_price[0]
                    if new_data[p]['max-demand'] > intermediate_monthly_bill[label_tariff][existing_mask_price]['max-demand']:
                        #print("Demand rate update: for mask {0}, {0} is greater than {2}".format(this_mask, new_data[p]['max-demand'], intermediate_monthly_bill[label_tariff][existing_mask_price]['max-demand'])) # debug

                        del intermediate_monthly_bill[label_tariff][existing_mask_price]
                        intermediate_monthly_bill[label_tariff][p] = new_data[p]
                else:  # This is the first time this mask has been seen: store it
                    intermediate_monthly_bill[label_tariff][p] = new_data[p]
        else:  # energy or fixed cost: apply SUM
            intermediate_monthly_bill[label_tariff] = (intermediate_monthly_bill[label_tariff][0] + new_data[0],
                                                       intermediate_monthly_bill[label_tariff][1] + new_data[1])

    def aggregate_monthly_bill(self, monthly_bill):
        """

        :param monthly_bill:
        :return: /
        """

        data_merge = None
        for m, data_per_label in list(monthly_bill.items()):
            if data_merge is None:
                data_merge = data_per_label
            else:
                for label_tariff, data_tariff in list(data_per_label.items()):
                    if self.type_tariffs_map[label_tariff] == ChargeType.DEMAND:  # take max
                        for p, data in list(data_tariff.items()):  # For each price -> dict (mask, max, date)
                            this_mask = data['mask']  # get the new data mask
                            existing_mask_price = [k for k, v in list(data_merge[label_tariff].items()) if v['mask'] == this_mask]

                            if len(existing_mask_price) > 0:  # this mask has already been seen: APPLY MAX
                                existing_mask_price = existing_mask_price[0]
                                if data['max-demand'] > data_merge[label_tariff][existing_mask_price]['max-demand']:
                                    #print("Demand rate update: for mask {1}, {0} is greater than {2}".format(this_mask, data, data_merge[label_tariff][p]))  # debug
                                    del data_merge[label_tariff][existing_mask_price]
                                    data_merge[label_tariff][p] = data
                            else:  # This is the first time this price has been seen: store it
                                data_merge[label_tariff][p] = data
                    else:  # sum
                        data_merge[label_tariff] = (data_merge[label_tariff][0] + data_tariff[0],
                                                    data_merge[label_tariff][1] + data_tariff[1])

        return data_merge


    @staticmethod
    def generate_type_tariff(type_tariff):
        return {'type': type_tariff,
                'list_blocks': []}
