#!/usr/bin/env python

"""
__author__   = 'Vikram Singh'
__email__    = 'simplyvikram@gmail.com'
"""

import argparse
from collections import defaultdict
from datetime import datetime, timedelta
import json


class Load:

    DATE_TIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'

    def __init__(self, id, customer_id, amount, time):
        self.id = id
        self.customer_id = customer_id
        self.amount = amount
        self.time = time

    @classmethod
    def create_load_from_dict(cls, d):
        return Load(
            id=d['id'],
            customer_id=d['customer_id'],
            amount=float(d['load_amount'][1:]),
            time=datetime.strptime(d['time'], cls.DATE_TIME_FORMAT)
        )

    def __repr__(self):
        return f'<Load id:{self.id} customer_id:{self.customer_id} ' \
               f'amount:{self.amount}, time:{self.time}>'


class LoadOutcome:

    def __init__(self, id, customer_id, accepted):
        self.id = id
        self.customer_id = customer_id
        self.accepted = accepted

    @classmethod
    def create_load_outcome_from_dict(cls, d):
        return LoadOutcome(
            id=d['id'],
            customer_id=d['customer_id'],
            accepted=d['accepted']
        )

    def __repr__(self):
        return f'<LoadOutcome id:{self.id} ' \
               f'customer_id:{self.customer_id} ' \
               f'accepted:{self.accepted}>'


class LoadManager:
    MAX_LOAD_AMOUNT_PER_WEEK = 20000
    MAX_LOAD_AMOUNT_PER_DAY = 5000
    MAX_NUM_LOADS_PER_DAY = 3

    def __init__(self):
        self.loads_cache = defaultdict(lambda: defaultdict(lambda: {}))
        # See below for an example of how the cache is used
        # {
        #     customer_id_1 : {
        #         id_A: Load_1_A,
        #         id_B: load_1_B,
        #     },
        #     customer_id_2 : {
        #         id_B: Load_2_B,
        #         id_C: load_2_C,  <- When val is a Load object, this means this load was accepted.
        #         id_D: None,      <- When val is None, this means that this load object was rejected.
        #                             We still want an an entry here, so that next time we see a new load
        #                               with the same load id and customer id, we know that the new load
        #                               needs to be ignored
        #     },
        # }

    def _get_customer_loads_from_cache(self, customer_id,):
        customer_loads = self.loads_cache[customer_id].values()
        customer_loads = list(filter(lambda c: c is not None, customer_loads))
        return customer_loads


    @staticmethod
    def get_day_start_end_times(some_datetime):
        day_start = datetime.combine(some_datetime, datetime.min.time())  # Go to start of day
        day_end = day_start + timedelta(days=1)                           # Go to end of day
        return day_start, day_end


    @staticmethod
    def get_week_start_end_times(some_datetime):
        week_start = some_datetime - timedelta(days=some_datetime.weekday())  # Go to Monday
        week_start = datetime.combine(week_start, datetime.min.time())        # Go to start of Monday
        week_end = week_start + timedelta(days=7)
        return week_start, week_end


    def _meets_max_load_criteria(self, load, start_time, end_time, max_load_amount):
        loads = self._get_customer_loads_from_cache(load.customer_id)

        amount_so_far = sum(
            [l.amount for l in loads if start_time <= l.time < end_time]
        )
        return True if (amount_so_far + load.amount) <= max_load_amount else False


    def _meets_max_num_load_criteria(self, load, start_time, end_time, max_num_loads):
        loads = self._get_customer_loads_from_cache(load.customer_id)

        num_loads_so_far = len(list(
            filter(lambda l: start_time <= l.time < end_time, loads)
        ))
        return True if num_loads_so_far < max_num_loads else False


    def _load_amount(self, load):
        """
        Processes a Load and returns a LoadOutcome object indicating whether the load
        was accepted or rejected. Returns None if the load needs to be ignored
        """

        print(f'\nProcessing load:{load}')

        day_start, day_end = LoadManager.get_day_start_end_times(load.time)
        week_start, week_end = LoadManager.get_week_start_end_times(load.time)

        if load.id in self.loads_cache[load.customer_id].keys():
            # This means we've already processed(accepted/rejected) a preceding load for this customer
            # with the same load id, so we will just ignore this load, by setting the LoadOutcome to be None
            print(f'  A load with the given id has already been processed for this customer, so this load is ignored')
            load_outcome = None

        elif all([
            self._meets_max_load_criteria(load, day_start, day_end, LoadManager.MAX_LOAD_AMOUNT_PER_DAY),
            self._meets_max_load_criteria(load, week_start, week_end, LoadManager.MAX_LOAD_AMOUNT_PER_WEEK),
            self._meets_max_num_load_criteria(load, day_start, day_end, LoadManager.MAX_NUM_LOADS_PER_DAY),
        ]):
            print(f'  This load, meets all the validation criteria, so we will accept it')
            self.loads_cache[load.customer_id][load.id] = load
            load_outcome = LoadOutcome(load.id, load.customer_id, accepted=True)

        else:
            print(f'  This load, does NOT meet some of the validation criteria, so we will reject it it')
            self.loads_cache[load.customer_id][load.id] = None
                                                          # Even if the load is rejected, we still want to save it
                                                          # in our cache dict, so that the next time, we see a load
                                                          # with the same customer_id and load_id, we know to ignore it
            load_outcome = LoadOutcome(load.id, load.customer_id, accepted=False)

        return load_outcome

    def process_loads(self, loads):
        """
        Process the loads in order, and generate a LoadOutcome for each of them.
        LoadOutcomes which are None(i.e which were ignored) are dropped
        """
        load_outcomes = [self._load_amount(load) for load in loads]
        load_outcomes = list(filter(lambda x: x is not None, load_outcomes))
        return load_outcomes


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Program to load funds into accounts')
    parser.add_argument(
        '-i', '--input_file',
        type=str, required=True,
        help='Input file, where each line, represent an amount load to be attempted on an account'
    )
    parser.add_argument(
        '-o', '--output_file',
        type=str, required=True,
        help='Output of the program, where each line represents the outcome of the processing'
             ' of each line of the input file. Some loads will need to be ignored.'
             ' So num of lines in input file will always have to be less'
             ' than number of lines in the output file',
    )
    args = parser.parse_args()

    with open(args.input_file, 'r') as f:
        print(f'Reading from input file: {args.input_file}')
        input_lines = f.read().splitlines()

    # Construct the list of Load objects from reading the input file line by line
    loads = [Load.create_load_from_dict(json.loads(l)) for l in input_lines]

    # Process the loads and collect the LoadOutcome list
    load_manager = LoadManager()
    load_outcomes = load_manager.process_loads(loads)

    load_outcomes_str_format = '{{"id":"{}","customer_id":"{}","accepted":{}}}\n'
    load_outcome_lines = [
        load_outcomes_str_format.format(o.id, o.customer_id, str(o.accepted).lower()) for o in load_outcomes
    ]

    # Write LoadOutcome list to output file line by line
    with open(args.output_file, 'w') as f:
        print(f'Writing to output file: {args.input_file}')
        f.writelines(load_outcome_lines)

    print('All done!')
