__author__ = 'Olivier Van Cutsem'

from abc import abstractmethod
from enum import Enum
from datetime import datetime
import calendar
import pandas as pd

# --------------- TARIFF structures --------------- #


class TariffType(Enum):
    FIX_CUSTOM_CHARGE = 'customer_fix_charge'
    ENERGY_CUSTOM_CHARGE = 'customer_energy_charge'
    DEMAND_CUSTOM_CHARGE_SEASON = 'customer_demand_charge_season'
    DEMAND_CUSTOM_CHARGE_TOU = 'customer_demand_charge_tou'
    PDP_ENERGY_CHARGE = 'pdp_event_energy_charge'
    PDP_ENERGY_CREDIT = 'pdp_non_event_energy_credit'
    PDP_DEMAND_CREDIT = 'pdp_non_event_demand_credit'


class TariffElemPeriod(Enum):

    MONTHLY = 'M'
    DAILY = 'D'
    HOURLY = '1h'
    HALFLY = '30min'
    QUARTERLY = '15min'


class TariffElemMetricUnit(Enum):
    EN_WH = 1
    DEMAND_W = 1
    EN_KWH = 1000.0
    DEMAND_KW = 1000.0


class TariffElemCostUnit(Enum):
    CENT = 0.01
    DOLLAR = 1


class TariffBase(object):
    """
    This abstract class represent the base of any tariffication structure.
    The main components are the starting and ending date of the structure.
    """

    def __init__(self, dates, unit_cost, name=None):

        # Starting and ending dates, as timestamps
        ts, te = dates
        self.__startdate = ts
        self.__enddate = te

        self.name = name
        self.unit_cost = unit_cost

    def compute_bill(self, df, data_col=None):
        """
        Compute the bill due to the power/energy consumption in df, for each billing period specified in billing_periods

        It outputs a dictionary formatted as follow:
        {
            "bill_period_label1": (float or dict, float),     -> the monthly 'metric' and its cost
            ...
        }

        :param df: a pandas dataframe containing power consumption timeseries
        :param billing_periods: a dictionary mapping the billing periods label to a tuple (t_start, t_end) of datetime,
        defining the period related to the billing label
        :return: a dictionary formatted as in this method signature
        """

        ret = {}

        # Select only the data in this tariff window
        start_sel = self.startdate
        start_sel = start_sel.replace(tzinfo=df.index[0].tzinfo)

        end_sel = self.enddate
        end_sel = end_sel.replace(tzinfo=df.index[0].tzinfo)

        mask = (df.index >= start_sel) & (df.index <= end_sel)
        df = df.loc[mask]

        # Loop over the months
        t_s = df.index[0]
        last_day_of_month = calendar.monthrange(t_s.year, t_s.month)[1]  # The last day of this month
        t_e = datetime(t_s.year, t_s.month, last_day_of_month, hour=23, minute=59, second=59, tzinfo=t_s.tzinfo)  # end of the current month
        t_e = min(df.index[-1], t_e)

        while t_s <= t_e:
            mask = (df.index >= t_s) & (df.index <= t_e)
            df_month = df.loc[mask]
            monthly_bill = self.compute_monthly_bill(df_month, data_col)
            ret[t_s.strftime("%Y-%m")] = monthly_bill

            # Prepare the next billing month
            month = t_e.month + 1
            year = t_e.year
            if month >= 13:
                month = 1
                year += 1

            t_s = datetime(year, month, 1, hour=0, minute=0, second=0, tzinfo=t_s.tzinfo)

            last_day_of_month = calendar.monthrange(year, month)[1]
            t_e = datetime(year, month, last_day_of_month, hour=23, minute=59, second=59, tzinfo=t_s.tzinfo)
            t_e = min(df.index[-1], t_e)

        return ret

    @abstractmethod
    def compute_monthly_bill(self, df, data_col=None):
        """
        Compute the monthly bill due to the power/energy consumption in df
        :param df: a pandas dataframe
        :param data_col: the column label containing the data
        :return: a tuple (float, float) -> (value, cost), representing the bill and the corresponding metric linked to the cost
        """

        pass

    @property
    def startdate(self):
        """
        GETTER of the tariff starting date
        :return: a timestamp
        """

        return self.__startdate

    @property
    def enddate(self):
        """
        GETTER of the tariff end date
        :return: a timestamp
        """

        return self.__enddate

    @abstractmethod
    def period_metric(self):
        pass

    @abstractmethod
    def get_price_from_timestamp(self, timestamp):
        pass


# --------------- FIXED TARIFF --------------- #


class FixedTariff(TariffBase):
    """
    Represent a tariff fixed over a given period (among TariffPeriod)
    """

    def __init__(self, dates, rate_value, unit_cost=TariffElemCostUnit.DOLLAR, bill_period=TariffElemPeriod.MONTHLY, name=None):
        """
        Constructor
        :param dates: see FixedTariff init
        :param bill_period: the period
        :param name: see FixedTariff init
        """

        super(FixedTariff, self).__init__(dates, unit_cost, name)

        self.__rate_period = bill_period
        self.__rate_value = rate_value

    def compute_monthly_bill(self, df, data_col=None):
        """
        Compute the monthly bill due to a fixed periodic cost

        :param df: a pandas dataframe
        :return: a tuple (float, float), representing the bill and the duration (in months)
        """
        first_day = df.index[0].day
        last_day = df.index[-1].day

        nb_days = last_day - first_day + 1
        nb_days_per_month = 365/12

        bill = 0

        if self.__rate_period == TariffElemPeriod.MONTHLY:
            bill = self.__rate_value * nb_days/nb_days_per_month  # a fraction of the month
        elif self.__rate_period == TariffElemPeriod.DAILY:
            bill = self.__rate_value * nb_days  # sum of each day

        return nb_days, bill

    def period_metric(self):
        return self.__rate_period

    def get_price_from_timestamp(self, timestamp):
        return self.__rate_value

# --------------- TOU TARIFFs --------------- #


class TimeOfUseTariff(TariffBase):
    """
    This class represents a tariff fixed over a given period (among TariffElemPeriod)
    """

    def __init__(self, dates, rate_schedule, unit_metric, unit_cost, name=None):
        """
        Constructor
        :param dates: see FixedTariff init
        :param rate_list:
        :param time_schedule: TODO
        :param name: see FixedTariff init
        """

        super(TimeOfUseTariff, self).__init__(dates, unit_cost, name)

        self.__schedule = rate_schedule  # A table mapping (month, day) to hourly rate index
        self.__unit_metric = unit_metric

    @abstractmethod
    def compute_monthly_bill(self, df, data_col=None):
        """
        idem super
        """

        pass

    @property
    def rate_schedule(self):
        return self.__schedule

    @property
    def unit_metric(self):
        return self.__unit_metric

    def period_metric(self):
        nb_periods_in_day = self.__schedule.periods_in_day

        # TODO: replace ifs by map
        if nb_periods_in_day == 24:
            return TariffElemPeriod.HOURLY
        elif nb_periods_in_day == 24 * 2:
            return TariffElemPeriod.HALFLY
        elif nb_periods_in_day == 24 * 4:
            return TariffElemPeriod.QUARTERLY
        else:
            return TariffElemPeriod.DAILY

    def get_price_from_timestamp(self, timestamp):
        return self.__schedule.get_from_timestamp(timestamp)

    @staticmethod
    def get_daily_price_dataframe(daily_rate, df_day):

        # Constructing the dataframe for an easier manipulation of time
        period_rate = len(daily_rate) / 24.0

        # In some cases the day might not be full: missing data or DST
        daily_prices = [daily_rate[int((df_day.index[i].hour + df_day.index[i].minute / 60.0) * period_rate)] for i in range(len(df_day.index))]
        data = {'date': df_day.index[:], 'price': daily_prices}
        df_prices = pd.DataFrame(data=data)
        df_prices.set_index('date')

        return df_prices


class TouDemandChargeTariff(TimeOfUseTariff):
    """
    This class represents a Time Of Use Demand Charge tariff
    """

    def __init__(self, dates, time_schedule, unit_metric=TariffElemMetricUnit.DEMAND_KW, unit_cost=TariffElemCostUnit.DOLLAR, name=None):
        """
        Constructor
        :param dates: see FixedTariff init
        :param rate_list: TODO
        :param time_schedule: TODO
        :param name: see FixedTariff init
        """

        super(TouDemandChargeTariff, self).__init__(dates, time_schedule, unit_metric, unit_cost, name)

    def compute_monthly_bill(self, df, data_col=None):
        """
        Compute the bill due to a TOU tariff
        :param df: a pandas dataframe
        :return: a tuple (dict, float) -> ({p1: (max_power_p1, time_max_p1), p2: (max_power_p2, time_max_p2), cost)
        """

        # Scaling the power unit and cost
        metric_unit_mult = float(self.unit_metric.value)
        metric_price_mult = float(self.unit_cost.value)

        max_per_set = {}

        # df is in kWh and demand in kW: convert to Power
        timestep_data = self.get_pd_timestep_data(df)

        for idx, df_day in df.groupby(df.index.date):
            daily_rate = self.rate_schedule.get_daily_rate(df_day.index[0])

            set_of_daily_prices = set(daily_rate)
            df_prices = self.get_daily_price_dataframe(daily_rate, df_day)

            power_coeff = 1
            if timestep_data == '15T':
                power_coeff = 4
            elif timestep_data == '30T':
                power_coeff = 2
            elif timestep_data == '60T' or timestep_data == 'H':
                power_coeff = 1

            for day_p in set_of_daily_prices:

                # Create the mask in the day for this price
                mask_price = df_prices['price'] == day_p
                mask_price = mask_price.tolist()

                date_max_period = None
                if data_col is not None:
                    df_masked = df_day.loc[mask_price, data_col]
                    if len(df_masked) > 0:
                        date_max_period = df_masked.idxmax()
                else:
                    df_masked = df_day.loc[mask_price]
                    if len(df_masked) > 0:
                        date_max_period = df_masked.idxmax()

                if date_max_period is None:
                    continue

                if data_col is not None:
                    max_power_period = df_day.loc[date_max_period, data_col] / metric_unit_mult
                else:
                    max_power_period = df_day[date_max_period] / metric_unit_mult

                max_power_period *= power_coeff  # from kWh to kW

                # Search for the same mask and update the value if a new mask
                mask_price24h = mask_price
                if len(mask_price) != len(daily_rate):  # if this price is already in the list, take the corresponding mask ...
                    price_key = metric_price_mult * day_p
                    if price_key in list(max_per_set.keys()):
                        mask_price24h = max_per_set[price_key]['mask']

                add_this_demand = True
                existing_mask_price = [k for k, v in list(max_per_set.items()) if v['mask'] == mask_price24h]
                if len(existing_mask_price) > 0:  # Find the identical mask over the day
                    existing_mask_price = existing_mask_price[0]
                    if max_power_period > max_per_set[existing_mask_price]['max-demand']:  # Check if the corresponding demand is greater
                        del max_per_set[existing_mask_price]  # delete the former value, and add it (after)
                    else:
                        add_this_demand = False

                # This is the first time this mask is seen OR this new demand is higher than the corresponding former: add it
                if add_this_demand:

                    if type(date_max_period) is not pd.Timestamp:
                        max_power_date = date_max_period[data_col].to_pydatetime()
                    else:
                        max_power_date = date_max_period.to_pydatetime()

                    # The mask must be 24 hour long:
                    # it might not be the case for the first and last day, and the DST
                    price_key = metric_price_mult * day_p

                    max_per_set[price_key] = {'mask': mask_price24h, 'max-demand': max_power_period, 'max-demand-date': max_power_date}

        return max_per_set

    def get_pd_timestep_data(self, df):
        """
        Return the most likely data frequency
        :return:
        """

        freq = 1

        # Dataframe is complete
        if df.index.freq is not None:
            return df.index.freq

        # Days are missing: loop through the day until getting a frequency
        for idx, df_day in df.groupby(df.index.date):
            if df_day.index.freq is not None:
                return df_day.index.freq
            elif len(df_day.index) > 2:  # need at least 3 dates
                return pd.infer_freq(df_day.index)

        return 1


class TouEnergyChargeTariff(TimeOfUseTariff):
    """
    This class represents a Time Of Use Energy Charge tariff
    """

    def __init__(self, dates, time_schedule, unit_metric=TariffElemMetricUnit.EN_KWH, unit_cost=TariffElemCostUnit.DOLLAR, name=None):
        """
        Constructor
        :param dates: see FixedTariff init
        :param time_schedule: TODO
        :param name: see FixedTariff init
        """

        super(TouEnergyChargeTariff, self).__init__(dates, time_schedule, unit_metric, unit_cost, name)

    def compute_monthly_bill(self, df, data_col=None):
        """
        Compute the bill due to a TOU tariff
        :param df: a pandas dataframe
        :return: a tuple (float, float) -> (cost, tot_energy)
        """

        # Iterates over the days
        energy = 0.0
        cost = 0.0

        # TODO: check for blockrate instead of assuming it's a float !

        for idx, df_day in df.groupby(df.index.date):

            daily_rate = self.rate_schedule.get_daily_rate(df_day.index[0])
            df_prices = self.get_daily_price_dataframe(daily_rate, df_day)

            # Unit and cost scale
            mult_energy_unit = float(self.unit_metric.value)
            mult_cost_unit = float(self.unit_cost.value)

            # Cumulate the energy over the month

            if data_col is not None:
                df_values_in_day = df_day.loc[:, data_col]
            else:
                df_values_in_day = df_day[:]

            energy += sum(df_values_in_day) / mult_energy_unit

            # Cumulate the bill over the month
            cost += sum(mult_cost_unit * df_values_in_day.multiply(df_prices.loc[:, 'price'].tolist())) / mult_energy_unit

        return energy, cost

