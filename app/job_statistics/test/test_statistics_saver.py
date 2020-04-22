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
            'started_at': (current_time + timedelta(seconds=1)).timestamp() * 1000,
            'finished_at': (current_time + timedelta(seconds=2)).timestamp() * 1000,
            'seconds_taken_from_created_to_running': 1,
            'seconds_taken_from_running_to_finished_or_error': 1,
            'final_state': 'FINISHED',
            'num_output_files': 2,
            'total_output_bytes': 100,
            'num_input_files': 3,
            'total_input_bytes': 300
        }

        job_record_dict_got = statistics_saver.get_job_record_dict(
            job_type=dict_must_be.get('job_type'),
            run_env_type=dict_must_be.get('run_env_type'),
            lsf_host=dict_must_be.get('lsf_host'),
            started_at=dict_must_be.get('started_at'),
            finished_at=dict_must_be.get('finished_at'),
            seconds_taken_from_created_to_running=dict_must_be.get('seconds_taken_from_created_to_running'),
            seconds_taken_from_running_to_finished_or_error=
            dict_must_be.get('seconds_taken_from_running_to_finished_or_error'),
            final_state=dict_must_be.get('final_state'),
            num_output_files=dict_must_be.get('num_output_files'),
            total_output_bytes=dict_must_be.get('total_output_bytes'),
            num_input_files=dict_must_be.get('num_input_files'),
            total_input_bytes=dict_must_be.get('total_input_bytes')
        )

        self.assertEqual(job_record_dict_got, dict_must_be, 'The job record dict was not generated correctly')
