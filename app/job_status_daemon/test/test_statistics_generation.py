"""
This Module tests the statistics generation of the status daemon
"""
import unittest
import shutil
from datetime import datetime, timedelta
from pathlib import Path
import os
import random

from app import create_app
from app.models import delayed_job_models
from app.job_status_daemon import daemon
from app.job_status_daemon.job_statistics import statistics_generator

class TestJobStatisticsGeneration(unittest.TestCase):
    """
    Class to test the generation of statistics by the status daemon
    """
    def setUp(self):
        self.flask_app = create_app()
        self.client = self.flask_app.test_client()

        with self.flask_app.app_context():
            delayed_job_models.delete_all_jobs()
            shutil.rmtree(daemon.AGENT_RUN_DIR, ignore_errors=True)

    def tearDown(self):
        with self.flask_app.app_context():
            delayed_job_models.delete_all_jobs()
            shutil.rmtree(daemon.AGENT_RUN_DIR, ignore_errors=True)

    def test_calculates_time_from_created_to_running(self):
        """
        test that it calculates the time from created to running
        """

        current_time = datetime.now()
        created_at = current_time
        seconds_must_be = 1.5
        started_at = created_at + timedelta(seconds=seconds_must_be)

        job = delayed_job_models.DelayedJob(
            id=f'Job-Finished',
            type='TEST',
            created_at=created_at,
            started_at=started_at
        )

        seconds_got = statistics_generator.get_seconds_from_created_to_queued(job)
        self.assertEqual(seconds_got, seconds_must_be,
                         msg='The seconds from created to queued were not calculated correctly!')

    def test_calculates_time_from_running_to_finished(self):
        """
        test that it calculates the time from running to finished
        """

        current_time = datetime.now()
        started_at = current_time
        seconds_must_be = 1.5
        finished_at = started_at + timedelta(seconds=seconds_must_be)

        job = delayed_job_models.DelayedJob(
            id=f'Job-Finished',
            type='TEST',
            started_at=started_at,
            finished_at=finished_at
        )

        seconds_got = statistics_generator.get_seconds_from_running_to_finished(job)
        self.assertEqual(seconds_got, seconds_must_be,
                         msg='The seconds from created to queued were not calculated correctly!')

    def test_calculates_correctly_the_number_of_input_files(self):
        """
        test that calculates correctly the number of input files
        """
        job = delayed_job_models.DelayedJob(
            id=f'Job-Finished',
            type='TEST'
        )

        tmp_dir = Path('tmp').joinpath(f'{random.randint(1, 1000000)}')
        os.makedirs(tmp_dir, exist_ok=True)

        input_files_desc = {
            'input1': str(Path.joinpath(tmp_dir, 'input1.txt')),
            'input2': str(Path.joinpath(tmp_dir, 'input2.txt'))
        }

        for key, path in input_files_desc.items():
            with open(path, 'w') as input_file:
                input_file.write(f'This is input file {key}')

                job_input_file = delayed_job_models.InputFile(
                    internal_path=str(path),
                )
                job.input_files.append(job_input_file)


        num_input_files_must_be = len(input_files_desc)
        num_input_files_got = statistics_generator.get_num_input_files_of_job(job)

        self.assertEqual(num_input_files_got, num_input_files_must_be,
                         msg='The number of input files was not calculated correctly')

        shutil.rmtree(tmp_dir)


    def test_calculates_correctly_the_size_of_input_files(self):
        """
        test that calculates correctly the size of input files
        """
        job = delayed_job_models.DelayedJob(
            id=f'Job-Finished',
            type='TEST'
        )

        tmp_dir = Path('tmp').joinpath(f'{random.randint(1, 1000000)}')
        os.makedirs(tmp_dir, exist_ok=True)

        input_files_desc = {
            'input1': str(Path.joinpath(tmp_dir, 'input1.txt')),
            'input2': str(Path.joinpath(tmp_dir, 'input2.txt'))
        }

        total_input_size_must_be = 0
        for key, path in input_files_desc.items():
            with open(path, 'w') as input_file:
                input_file.write(f'This is input file {key}')

                job_input_file = delayed_job_models.InputFile(
                    internal_path=str(path),
                )
                job.input_files.append(job_input_file)

            current_file_size = os.path.getsize(path)
            total_input_size_must_be += current_file_size

        total_input_size_got = statistics_generator.get_total_bytes_of_input_files_of_job(job)

        self.assertEqual(total_input_size_got, total_input_size_must_be,
                         msg='The size of the input files was not calculated correctly')

        shutil.rmtree(tmp_dir)

    # def test_calculates_correctly_the_number_of_output_files(self):
    #     """
    #     test that calculates correctly the number of output files
    #     """
    #     job = delayed_job_models.DelayedJob(
    #         id=f'Job-Finished',
    #         type='TEST'
    #     )
    #
    #     tmp_dir = Path('tmp').joinpath(f'{random.randint(1, 1000000)}')
    #     os.makedirs(tmp_dir, exist_ok=True)
    #
    #     input_files_desc = {
    #         'input1': str(Path.joinpath(tmp_dir, 'input1.txt')),
    #         'input2': str(Path.joinpath(tmp_dir, 'input2.txt'))
    #     }
    #
    #     for key, path in input_files_desc.items():
    #         with open(path, 'w') as input_file:
    #             input_file.write(f'This is input file {key}')
    #
    #             job_input_file = delayed_job_models.InputFile(
    #                 internal_path=str(path),
    #             )
    #             job.input_files.append(job_input_file)
    #
    #
    #     num_input_files_must_be = len(input_files_desc)
    #     num_input_files_got = statistics_generator.get_num_input_files_of_job(job)
    #
    #     self.assertEqual(num_input_files_got, num_input_files_must_be,
    #                      msg='The number of input files was not calculated correctly')







