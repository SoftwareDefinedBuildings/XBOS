__author__ = 'Olivier Van Cutsem'

from ..cost_calculator.tariff_structure import *
from ..cost_calculator.rate_structure import *

import time
from datetime import datetime
import requests
import json
import pytz
import os

# ----------- FUNCTIONS SPECIFIC TO OpenEI REQUESTS -------------- #
THIS_PATH = os.path.dirname(os.path.abspath(__file__)) + '/'
PDP_PATH = os.path.dirname(os.path.abspath(__file__)) + '/'

SUFFIX_REVISED = '_revised'  # this is the suffix we added to the json filename after correctly the OpenEI data manually


class OpenEI_tariff(object):

    URL_OPENEI = 'https://api.openei.org/utility_rates'
    API_KEY = 'BgEcyD9nM0C24J2vL4ezN7ZNAllII0vKA9l7UEBu'
    FORMAT = 'json'
    VERSION = 'latest'
    DIRECTION_SORT = 'asc'
    DETAIL = 'full'
    LIMIT = '500'
    ORDER_BY_SORT = 'startdate'

    def __init__(self, utility_id, sector, tariff_rate_of_interest, distrib_level_of_interest='Secondary', phasewing='Single', tou=False, pdp=True, option_mandatory=None, option_exclusion=None):

        self.req_param = {}

        # Request param
        self.req_param['api_key'] = self.API_KEY
        self.req_param['eia'] = utility_id
        self.req_param['sector'] = sector

        self.req_param['format'] = self.FORMAT
        self.req_param['version'] = self.VERSION

        self.req_param['direction'] = self.DIRECTION_SORT
        self.req_param['detail'] = self.DETAIL
        self.req_param['limit'] = self.LIMIT
        self.req_param['orderby'] = self.ORDER_BY_SORT

        # Post-req filter
        self.tariff_rate_of_interest = tariff_rate_of_interest
        self.distrib_level_of_interest = distrib_level_of_interest
        self.phase_wing = phasewing
        self.tou = tou
        self.option_exclusion = option_exclusion
        self.option_mandatory = option_mandatory

        self.pdp_participate = pdp

        # The raw filtered answer from an API call
        self.data_openei = None
        self.pdp_events = []

    def set_pdp_events(self, pdp_events_dict):
        self.pdp_events = pdp_events_dict

    def call_api(self, store_as_json=None):

        r = requests.get(self.URL_OPENEI, params=self.req_param)
        data_openei = r.json()
        data_filtered = []

        for data_block in data_openei['items']:
            print(data_block['name'])
            # Check the tariff name, this is stored in the field "name"
            if self.tariff_rate_of_interest not in data_block['name'] and self.tariff_rate_of_interest + '-' not in data_block['name']:
                continue
            print((" - {0}".format(data_block['name'])))

            # Check the wiring option
            if self.phase_wing is not None:
                if 'phasewiring' in list(data_block.keys()):
                    if not(self.phase_wing in data_block['phasewiring']):
                        continue
                else:  # check the title if this field is missing
                    if self.phase_wing not in data_block['name']:
                        continue

            # Check the grid level option
            if self.distrib_level_of_interest is not None:
                if self.distrib_level_of_interest not in data_block['name']:
                    continue

            print((" -- {0}".format(data_block['name'])))
            # Check the Time of Use option
            if (self.tou and 'TOU' not in data_block['name']) or (not self.tou and 'TOU' in data_block['name']):
                continue

            # Ensure some options on the rate:
            if self.option_mandatory is not None:
                continue_block = False
                for o in self.option_mandatory:
                    if o not in data_block['name']:
                        continue_block = True
                        break
                if continue_block:
                    continue

            # Exclude some options on the rate
            if self.option_exclusion is not None:
                continue_block = False
                for o in self.option_exclusion:
                    if o in data_block['name']:
                        continue_block = True
                        break
                if continue_block:
                    continue

            #print(" -------> {0}".format(data_block['name']))
            # The conditions are fulfilled: add this block
            data_filtered.append(data_block)

        # Make sure we work with integer timestamps
        for rate_data in data_filtered:
            # Starting time
            if not (type(rate_data['startdate']) is int):
                t_s = time.mktime(
                    datetime.strptime(rate_data['startdate'],
                                      '%Y-%m-%dT%H:%M:%S.000Z').timetuple())  # Always specified
                rate_data['startdate'] = t_s

            # Ending time
            if 'enddate' in list(rate_data.keys()):
                if not (type(rate_data['enddate']) is int):
                    t_e = time.mktime(datetime.strptime(rate_data['enddate'],
                                                        '%Y-%m-%dT%H:%M:%S.000Z').timetuple())  # maybe not specified - assumed it's until now
                    rate_data['enddate'] = t_e
            else:
                rate_data['enddate'] = time.time()

        # Make sure that the dates are consecutive
        for i in range(len(data_filtered) - 1):
            data_cur = data_filtered[i]
            data_next = data_filtered[i + 1]
            # Replace END time of the current elem by the START time of the next one if necessary
            data_cur['enddate'] = min(data_next['startdate'], data_cur['enddate'])

        # Re-encode the date as human
        for block in data_filtered:
            block['startdate'] = datetime.fromtimestamp(block['startdate'], tz=pytz.timezone("UTC")).strftime('%Y-%m-%dT%H:%M:%S.000Z')
            block['enddate'] = datetime.fromtimestamp(block['enddate'], tz=pytz.timezone("UTC")).strftime('%Y-%m-%dT%H:%M:%S.000Z')

        # Store internally the filtered result
        self.data_openei = data_filtered

        # Store the result of this processed API request in a JSON file that has the name built from the tariff info
        if store_as_json is not None:
            filename = self.json_filename
            with open(THIS_PATH+filename+'.json', 'w') as outfile:
                json.dump(data_filtered, outfile, indent=2, sort_keys=True)

    def read_from_json(self, filename=None):
        """
        Read tariff data from a JSON file to build the internal structure. The JSON file
        :return:
         - 0 if the data has been loaded from the json successfully,
         - 1 if the data couldn't be laod from the json file
         - 2 if the file couldn't be read
        """
        try:
            if filename == None:
                filename = THIS_PATH+self.json_filename+SUFFIX_REVISED+'.json'
            with open(filename, 'r') as input_file:
                try:
                    self.data_openei = json.load(input_file)
                except ValueError:
                    print('cant parse json')
                    return 1
        except:
            print('cant open file')
            return 2

        # Encode the start/end dates as integers
        for block in self.data_openei:
            block['enddate'] = datetime.strptime(block['enddate'], '%Y-%m-%dT%H:%M:%S.000Z').replace(tzinfo=pytz.timezone('UTC'))
            block['startdate'] = datetime.strptime(block['startdate'], '%Y-%m-%dT%H:%M:%S.000Z').replace(tzinfo=pytz.timezone('UTC'))

        return 0 # everything went well

    def checkIfPDPDayPresent(self, utilityId, st, et):
        for event in self.pdp_events:
            if event['utility_id'] == utilityId and event['start_date'] == st and event['end_date'] == et:
                return True
        return False

    @property
    def json_filename(self):

        # Conditional field: TOU or nothing
        if_tou = ''
        if self.tou:
            if_tou = '_TOU'

        # Wiring
        phase_info = ''
        if self.phase_wing is not None:
            phase_info = '_phase'+self.phase_wing

        # Grid level
        gridlevel_info = ''
        if self.distrib_level_of_interest is not None:
            gridlevel_info = '_gridlevel'+self.distrib_level_of_interest

        return 'u'+self.req_param['eia']+'_'+self.req_param['sector']+'_'+self.tariff_rate_of_interest+if_tou+phase_info+gridlevel_info

# --- Inject data from OpenEI_tariff object to the Bill Calculator

def tariff_struct_from_openei_data(openei_tarif_obj, bill_calculator, pdp_event_filenames="PDP_events.json"):
    """
    Analyze the content of an OpenEI request in order to fill a CostCalculator object
    :param openei_tarif_obj: an instance of OpenEI_tariff that already call the API
    :param bill_calculator: an (empty) instance of CostCalculator
    :return: /
    """

    tariff_struct = {}

    # Analyse each block
    for block_rate in openei_tarif_obj.data_openei:

        # Tariff starting and ending dates
        if type(block_rate['startdate']) is not datetime:
            block_rate['startdate'] = datetime.strptime(block_rate['startdate'], '%Y-%m-%dT%H:%M:%S.000Z').replace(
                tzinfo=pytz.timezone('UTC'))
        if type(block_rate['enddate']) is not datetime:
            block_rate['enddate'] = datetime.strptime(block_rate['enddate'], '%Y-%m-%dT%H:%M:%S.000Z').replace(
                tzinfo=pytz.timezone('UTC'))

        tariff_dates = (block_rate['startdate'], block_rate['enddate'])

        # --- Fix charges
        if 'fixedchargefirstmeter' in list(block_rate.keys()):
            tariff_fix = block_rate['fixedchargefirstmeter']

            period_fix_charge = TariffElemPeriod.MONTHLY

            if '/day' in block_rate['fixedchargeunits']:
                period_fix_charge = TariffElemPeriod.DAILY

            bill_calculator.add_tariff(FixedTariff(tariff_dates, tariff_fix, period_fix_charge), str(TariffType.FIX_CUSTOM_CHARGE.value))

        # --- Demand charges: flat
        tariff_flatdemand_obj = get_flatdemand_obj_from_openei(block_rate)

        if tariff_flatdemand_obj is not None:
            bill_calculator.add_tariff(TouDemandChargeTariff(tariff_dates, tariff_flatdemand_obj),
                                       str(TariffType.DEMAND_CUSTOM_CHARGE_SEASON.value))

        # --- Energy charges
        tariff_energy_obj = get_energyrate_obj_from_openei(block_rate)

        if tariff_energy_obj is not None:
            bill_calculator.add_tariff(TouEnergyChargeTariff(tariff_dates, tariff_energy_obj), str(TariffType.ENERGY_CUSTOM_CHARGE.value))

        # --- Demand charges: tou
        tariff_toudemand_obj = get_demandrate_obj_from_openei(block_rate)

        if tariff_toudemand_obj is not None:
            bill_calculator.add_tariff(TouDemandChargeTariff(tariff_dates, tariff_toudemand_obj), str(TariffType.DEMAND_CUSTOM_CHARGE_TOU.value))

        if openei_tarif_obj.pdp_participate:
            # --- PDP credits for energy - todo: remove the pdp days
            tariff_pdp_credit_energy_obj = get_pdp_credit_energyrate_obj_from_openei(block_rate)

            if tariff_pdp_credit_energy_obj is not None:
                bill_calculator.add_tariff(TouEnergyChargeTariff(tariff_dates, tariff_pdp_credit_energy_obj),
                                           str(TariffType.PDP_ENERGY_CREDIT.value))

            # --- PDP credits for demand
            tariff_pdp_credit_demand_obj = get_pdp_credit_demandrate_obj_from_openei(block_rate)

            if tariff_pdp_credit_demand_obj is not None:
                bill_calculator.add_tariff(TouDemandChargeTariff(tariff_dates, tariff_pdp_credit_demand_obj),
                                           str(TariffType.PDP_DEMAND_CREDIT.value))
                # --- PDP credits for demand

    # Other useful information, beside the tariff
    # Loop over all the blocks to be sure, maybe such fields are missing in some ..
    for block_rate in openei_tarif_obj.data_openei:
        if 'peakkwcapacitymax' in list(block_rate.keys()):
            bill_calculator.tariff_max_kw = block_rate['peakkwcapacitymax']
        if 'peakkwcapacitymin' in list(block_rate.keys()):
            bill_calculator.tariff_min_kw = block_rate['peakkwcapacitymin']

        if 'peakkwhusagemax' in list(block_rate.keys()):
            bill_calculator.tariff_max_kwh = block_rate['peakkwhusagemax']
        if 'peakkwhusagemin' in list(block_rate.keys()):
            bill_calculator.tariff_min_kwh = block_rate['peakkwhusagemin']

    # Analyse PdP events

    if openei_tarif_obj.pdp_participate:
        pdp_data = []
        try:
            pdp_data = populate_pdp_events_from_json(openei_tarif_obj, pdp_event_filenames=pdp_event_filenames)
        except EnvironmentError:
            print("PdP events: can't open file")

        pdp_data_filter = [event for event in pdp_data if event['utility_id'] == int(openei_tarif_obj.req_param['eia'])]
        for pdp_event in pdp_data_filter:
            pdp_dates = datetime.strptime(pdp_event['start_date'], '%Y-%m-%dT%H:%M:%S-08:00').replace(tzinfo=pytz.timezone('US/Pacific')), datetime.strptime(
                pdp_event['end_date'], '%Y-%m-%dT%H:%M:%S-08:00').replace(tzinfo=pytz.timezone('US/Pacific'))
            tariff_pdp_obj = get_pdp_energycharge(openei_tarif_obj, pdp_dates[0])
            if tariff_pdp_obj is not None:
                bill_calculator.add_tariff(TouEnergyChargeTariff(pdp_dates, tariff_pdp_obj),
                                           str(TariffType.PDP_ENERGY_CHARGE.value))

def populate_pdp_events_from_json(openei_tarif_obj, pdp_event_filenames='PDP_events.json'):
    empty = []
    if not os.path.exists(PDP_PATH+pdp_event_filenames):
        with open(PDP_PATH+pdp_event_filenames, 'w') as pdp_file:
            json.dump(empty, pdp_file)
    with open(PDP_PATH+pdp_event_filenames, 'r') as pdp_file:
        try:
            pdp_data = json.load(pdp_file)
            openei_tarif_obj.set_pdp_events(pdp_data)
            return pdp_data
        except ValueError:
            print("PdP events: can't parse json")

def update_pdp_json(openei_tarif_obj, pdp_dict, pdp_event_filenames='PDP_events.json'):
    if cmp(openei_tarif_obj.pdp_events, pdp_dict) != 0:
        with open(PDP_PATH + pdp_event_filenames, 'w') as pdp_fp:
            json.dump(pdp_dict, pdp_fp)
        openei_tarif_obj.set_pdp_events(pdp_dict)
        return True
    return False

def get_energyrate_obj_from_openei(open_ei_block):

    # TODO later: use BlockRate instead of assuming it's a float !
    if 'energyratestructure' not in list(open_ei_block.keys()):
        return None

    en_rate_list = open_ei_block['energyratestructure']

    weekdays_schedule = open_ei_block['energyweekdayschedule']
    weekends_schedule = open_ei_block['energyweekendschedule']

    rate_struct = read_tou_rates(en_rate_list, weekdays_schedule, weekends_schedule)

    if rate_struct != {}:
        return TouRateSchedule(rate_struct)
    else:
        return None


def get_flatdemand_obj_from_openei(open_ei_block):

    rate_struct = {}
    if 'flatdemandstructure' in list(open_ei_block.keys()):  # there is a flat demand rate
        dem_rate_list = open_ei_block['flatdemandstructure']
        dem_time_schedule_month = open_ei_block['flatdemandmonths']

        rate_struct = read_flat_rates(dem_rate_list, dem_time_schedule_month)

    if rate_struct != {}:
        return TouRateSchedule(rate_struct)
    else:
        return None


def get_demandrate_obj_from_openei(open_ei_block):

    if 'demandratestructure' not in list(open_ei_block.keys()):
        return None

    demand_rate_list = open_ei_block['demandratestructure']

    weekdays_schedule = open_ei_block['demandweekdayschedule']
    weekends_schedule = open_ei_block['demandweekendschedule']

    rate_struct = read_tou_rates(demand_rate_list, weekdays_schedule, weekends_schedule)

    if rate_struct != {}:
        return TouRateSchedule(rate_struct)
    else:
        return None


def read_tou_rates(rate_map, weekdays_schedule, weekends_schedule):

    ret = {}

    for m_i in range(12):

        already_added = False
        daily_weekdays_rate = [rate_map[x][0]['rate'] for x in weekdays_schedule[m_i]]
        daily_weekends_rate = [rate_map[x][0]['rate'] for x in weekends_schedule[m_i]]

        # Check if this schedule is already present
        for m_group_lab, m_group_data in list(ret.items()):
            if daily_weekdays_rate == m_group_data[TouRateSchedule.DAILY_RATE_KEY]['weekdays'][
                TouRateSchedule.RATES_KEY] and daily_weekends_rate == \
                    m_group_data[TouRateSchedule.DAILY_RATE_KEY]['weekends'][TouRateSchedule.RATES_KEY]:
                m_group_data[TouRateSchedule.MONTHLIST_KEY].append(m_i + 1)
                already_added = True
                break

        if not already_added:
            ret['m_' + str(m_i + 1)] = {TouRateSchedule.MONTHLIST_KEY: [m_i + 1],
                                                TouRateSchedule.DAILY_RATE_KEY: {
                                                    'weekdays': {
                                                        TouRateSchedule.DAYSLIST_KEY: [0, 1, 2, 3, 4],
                                                        TouRateSchedule.RATES_KEY: daily_weekdays_rate
                                                    },
                                                    'weekends': {
                                                        TouRateSchedule.DAYSLIST_KEY: [5, 6],
                                                        TouRateSchedule.RATES_KEY: daily_weekends_rate}
                                                }
                                                }

    return ret


def read_flat_rates(rate_map, month_schedule):
    """

    :param rate_map:
    :param month_schedule:
    :return:
    """
    map_month_label = {1: 'winter', 0: 'summer'}
    rate_struct = {}

    for rate_idx in range(len(rate_map)):
        months_list = [i + 1 for i, j in enumerate(month_schedule) if j == rate_idx]
        rate_struct[map_month_label[rate_idx]] = {TouRateSchedule.MONTHLIST_KEY: months_list,
                                                  TouRateSchedule.DAILY_RATE_KEY: {
                                                      'allweek': {
                                                          TouRateSchedule.DAYSLIST_KEY: list(range(7)),
                                                          TouRateSchedule.RATES_KEY: 24 * [
                                                              rate_map[rate_idx][0]['rate']]
                                                      }
                                                  }
                                                  }

    return rate_struct

# -- PDP manipulation

def get_pdp_energycharge(openei_tarif_obj, date_start_event):
    """

    :param openei_tarif_obj:
    :param daterange:
    :return:
    """

    # Search the corresponding block in the OpenEI data
    block_l = [data for data in openei_tarif_obj.data_openei if data['startdate'] <= date_start_event <= data['enddate']]

    if len(block_l) > 0:  # no block found ..
        block = block_l[0]

        if 'pdp_charge_energy' not in block:  # this tariff doesn't support PDP
            return None

        energy_charge = block['pdp_charge_energy']

        rate_struct = {}
        rate_struct['allmonth'] = {TouRateSchedule.MONTHLIST_KEY: list(range(1,13)),
                                                  TouRateSchedule.DAILY_RATE_KEY: {
                                                      'allweek': {
                                                          TouRateSchedule.DAYSLIST_KEY: list(range(7)),
                                                          TouRateSchedule.RATES_KEY: energy_charge
                                                      }
                                                  }
                                                  }
        return TouRateSchedule(rate_struct)
    else:
        return None

def get_pdp_credit_energyrate_obj_from_openei(open_ei_block):
    """

    :param block_rate:
    :return:
    """

    # TODO later: use BlockRate instead of assuming it's a float !
    if 'pdp_credit_energyratestructure' not in list(open_ei_block.keys()):
        return None

    en_rate_list = open_ei_block['pdp_credit_energyratestructure']

    weekdays_schedule = open_ei_block['energyweekdayschedule']
    weekends_schedule = open_ei_block['energyweekendschedule']

    rate_struct = read_tou_rates(en_rate_list, weekdays_schedule, weekends_schedule)

    if rate_struct != {}:
        return TouRateSchedule(rate_struct)
    else:
        return None

def get_pdp_credit_demandrate_obj_from_openei(open_ei_block):
    """

    :param block_rate:
    :return:
    """

    if 'pdp_credit_demandratestructure' not in list(open_ei_block.keys()):
        return None

    pdp_demand_credit_list = open_ei_block['pdp_credit_demandratestructure']

    rate_struct = {}

    if 'demandweekdayschedule' in list(open_ei_block.keys()):  # TOU demand
        weekdays_schedule = open_ei_block['demandweekdayschedule']
        weekends_schedule = open_ei_block['demandweekendschedule']
        rate_struct = read_tou_rates(pdp_demand_credit_list, weekdays_schedule, weekends_schedule)

    elif 'flatdemandstructure' in list(open_ei_block.keys()): # flat demand
        monthly_schedule = open_ei_block['flatdemandmonths']
        rate_struct = read_flat_rates(pdp_demand_credit_list, monthly_schedule)

    if rate_struct != {}:
        return TouRateSchedule(rate_struct)
    else:
        return None
