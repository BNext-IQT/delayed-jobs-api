"""
This Module tests the statistics saver
"""
import unittest
from datetime import datetime, timedelta

from app.job_statistics import statistics_saver

class TestStatisticsSaver(unittest.TestCase):
    """
    Class to test the statistics saver
    """
    def test_generates_the_correct_json_for_a_job_record(self):
        """
        Tests that it generates the correct json for a job record to be sent to elasticsearch
        """
        current_time = datetime.now()

        dict_must_be = {
            'job_type': 'TEST',
            'run_env_type': 'DEV',
            'lsf_host': 'some_host',
            'started_at': (current_time + timedelta(seconds=1)).timestamp() * 1000
        }

        job_record_dict_got = statistics_saver.get_job_record_dict(
            job_type=dict_must_be.get('job_type'),
            run_env_type=dict_must_be.get('run_env_type'),
            lsf_host=dict_must_be.get('lsf_host'),
            started_at=dict_must_be.get('started_at'),
        )

        self.assertEqual(job_record_dict_got, dict_must_be, 'The job record dict was not generated correctly')
