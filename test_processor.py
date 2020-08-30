#!/usr/bin/env python

"""
__author__   = 'Vikram Singh'
__email__    = 'simplyvikram@gmail.com'
"""

from collections import namedtuple
import datetime as dt
from unittest import mock, TestCase

from processor import Load, LoadOutcome, LoadManager


LoadAndOutcomeTuple = namedtuple(
    'LoadAndOutcomeTuple', ['id', 'customer_id', 'amount', 'time',  'status']
)                         # status can be True to indicate that this Load was Accepted
                          # status can be False to indicate that this Load was Rejected
                          # status can be None to indicate that this load was ignored

SAMPLE_DATETIME = dt.datetime(2020, 8, 28, 14, 18, 47, 569)  # Friday


class TestProcessor(TestCase):

    def _validate_load_and_outcome(self, load_and_outcome_tuples):

        # Create the Load objects from the tuples passed
        loads = [
            Load(x.id, x.customer_id, x.amount, x.time) for x in load_and_outcome_tuples
        ]

        # Now we will try to parse expected outcomes from the tuples list
        expected_load_outcomes = load_and_outcome_tuples
        # First only fetch tuples which were accepted/rejected
        expected_load_outcomes = list(
            filter(lambda x:  isinstance(x.status, bool), expected_load_outcomes)
        )
        # From the filtered tuples now create the LoadOutcome objects
        expected_load_outcomes = [
            LoadOutcome(x.id, x.customer_id, x.status) for x in expected_load_outcomes
        ]
        actual_load_outcomes = LoadManager().process_loads(loads)

        self.assertEqual(len(actual_load_outcomes), len(expected_load_outcomes))

        for i in range(len(actual_load_outcomes)):

            left = actual_load_outcomes[i]
            right = expected_load_outcomes[i]
            print(f'\n\noutcome:{left}\nexpected:{right}')

            self.assertEqual(left.id, right.id)
            self.assertEqual(left.customer_id, right.customer_id)
            self.assertEqual(left.accepted, right.accepted)


    def test_max_amount_per_day(self):

        load_and_outcome_tuples = [
            # Try to do loads for two customers below the daily limit
            LoadAndOutcomeTuple(101, 600, 4999.99, SAMPLE_DATETIME + dt.timedelta(minutes=10), status=True),
            LoadAndOutcomeTuple(102, 700, 4999.99, SAMPLE_DATETIME + dt.timedelta(minutes=20), status=True),
            LoadAndOutcomeTuple(103, 600, 0.01, SAMPLE_DATETIME + dt.timedelta(minutes=30), status=True),
            LoadAndOutcomeTuple(104, 700, 0.01, SAMPLE_DATETIME + dt.timedelta(minutes=40), status=True),

            # As soon as the loaded per day starts to increase from the daily limit
            # the status for the load should get marked as False
            LoadAndOutcomeTuple(105, 600, 0.01, SAMPLE_DATETIME + dt.timedelta(minutes=50), status=False),
            LoadAndOutcomeTuple(106, 700, 0.01, SAMPLE_DATETIME + dt.timedelta(minutes=60), status=False),
        ]
        self._validate_load_and_outcome(load_and_outcome_tuples)


    def test_max_amount_per_week(self):

        load_and_outcome_tuples = [
            # Try a few loads for the current week all below the weekly limit
            LoadAndOutcomeTuple(101, 600, 4999.99, SAMPLE_DATETIME - dt.timedelta(days=0), status=True),
            LoadAndOutcomeTuple(102, 600, 4999.99, SAMPLE_DATETIME - dt.timedelta(days=1), status=True),
            LoadAndOutcomeTuple(103, 600, 4999.99, SAMPLE_DATETIME - dt.timedelta(days=2), status=True),
            LoadAndOutcomeTuple(104, 600, 4999.99, SAMPLE_DATETIME - dt.timedelta(days=3), status=True),

            # If the weekly limit is being exceeded the load should be rejected
            LoadAndOutcomeTuple(105, 600, 4999.99, SAMPLE_DATETIME - dt.timedelta(days=4), status=False),

            # Try adding a few smaller loads, to just reach the weekly limit, they should all be accepted
            LoadAndOutcomeTuple(106, 600, 0.02, SAMPLE_DATETIME - dt.timedelta(days=4), status=True),
            LoadAndOutcomeTuple(107, 600, 0.02, SAMPLE_DATETIME - dt.timedelta(days=4), status=True),

            # Since we are at the weekly limit, even the smalled load should get rejected
            LoadAndOutcomeTuple(108, 600, 0.01, SAMPLE_DATETIME - dt.timedelta(days=4), status=False),

            # But if we go back to previous week, we should be able to hit the daily limit again
            LoadAndOutcomeTuple(109, 600, 5000, SAMPLE_DATETIME - dt.timedelta(days=5), status=True),
            LoadAndOutcomeTuple(110, 600, 0.01, SAMPLE_DATETIME - dt.timedelta(days=5), status=False),
            LoadAndOutcomeTuple(111, 600, 5000, SAMPLE_DATETIME - dt.timedelta(days=7), status=True),
            LoadAndOutcomeTuple(112, 600, 5000, SAMPLE_DATETIME - dt.timedelta(days=8), status=True),
        ]
        self._validate_load_and_outcome(load_and_outcome_tuples)


    def test_num_loads_per_day(self):

        load_and_outcome_tuples = [
            # Try doing a few small Loads for the day
            LoadAndOutcomeTuple(101, 600, 0.10, SAMPLE_DATETIME - dt.timedelta(minutes=0), status=True),
            LoadAndOutcomeTuple(102, 600, 0.10, SAMPLE_DATETIME - dt.timedelta(minutes=1), status=True),
            LoadAndOutcomeTuple(103, 600, 0.10, SAMPLE_DATETIME - dt.timedelta(minutes=2), status=True),

            # Since we have exceeded the nax number of transactions allowed per day,
            # the next Load no matter how small it is, should fail
            LoadAndOutcomeTuple(104, 600, 0.10, SAMPLE_DATETIME - dt.timedelta(minutes=3), status=False),
            LoadAndOutcomeTuple(105, 600, 1.00, SAMPLE_DATETIME - dt.timedelta(minutes=4), status=False),
            LoadAndOutcomeTuple(106, 600, 100, SAMPLE_DATETIME - dt.timedelta(minutes=5), status=False),
            LoadAndOutcomeTuple(107, 600, 1000, SAMPLE_DATETIME - dt.timedelta(minutes=6), status=False),
        ]
        self._validate_load_and_outcome(load_and_outcome_tuples)


    def test_ignored_loads(self):

        load_and_outcome_tuples = [
            # Even if a load fails, subsequent loads with the same id and customer_id will have to be
            # ignored even if they meet the daily/weekly criteria
            LoadAndOutcomeTuple(101, 600, 5001, SAMPLE_DATETIME - dt.timedelta(minutes=0), status=False),
            LoadAndOutcomeTuple(101, 600, 100, SAMPLE_DATETIME - dt.timedelta(minutes=1), status=None),
            LoadAndOutcomeTuple(101, 600, 100, SAMPLE_DATETIME - dt.timedelta(minutes=2), status=None),

        ]
        self._validate_load_and_outcome(load_and_outcome_tuples)

        load_and_outcome_tuples = [
            # If a load succeeds, subsequent loads with the same id and customer_id will have to
            # be ignored regardless of whether they meet the daily/weekly criteria
            LoadAndOutcomeTuple(101, 600, 5000, SAMPLE_DATETIME - dt.timedelta(minutes=0), status=True),
            LoadAndOutcomeTuple(101, 600, 100, SAMPLE_DATETIME - dt.timedelta(minutes=1), status=None),
            LoadAndOutcomeTuple(101, 600, 100, SAMPLE_DATETIME - dt.timedelta(minutes=2), status=None),

        ]
        self._validate_load_and_outcome(load_and_outcome_tuples)
