"""
Tests for the job deletion
"""
import unittest
import os
from pathlib import Path
import shutil
import datetime
import random
import string

from app import create_app
from app.namespaces.models import delayed_job_models


class TestExpiredJobDeletion(unittest.TestCase):
    """
    Class to test the deletion of expired jobs
    """

    TEST_RUN_DIR_NAME = 'test_run_dir'
    ABS_RUN_DIR_PATH = str(Path(TEST_RUN_DIR_NAME).resolve())
    OUT_RUN_DIR_NAME = 'test_out_dir'
    ABS_OUT_DIR_PATH = str(Path(OUT_RUN_DIR_NAME).resolve())

    def setUp(self):
        self.flask_app = create_app()
        self.client = self.flask_app.test_client()

        os.makedirs(self.ABS_RUN_DIR_PATH, exist_ok=True)
        os.makedirs(self.ABS_OUT_DIR_PATH, exist_ok=True)

    def tearDown(self):

        with self.flask_app.app_context():
            delayed_job_models.delete_all_jobs()

        shutil.rmtree(self.ABS_RUN_DIR_PATH)
        shutil.rmtree(self.ABS_OUT_DIR_PATH)

    def simulate_inputs_to_job(self, job, job_run_dir):
        """
        Creates some input files and adds it to the job object
        :param job: job to add the input files to
        :param job_run_dir: directory where the job runs
        """
        inputs_path = os.path.join(job_run_dir, 'inputs')
        for i in range(1, 5):
            input_path = os.path.join(inputs_path, f'input{i}.txt')
            with open(inputs_path, 'w') as input_file:
                input_file.write(f'This is input {i}')

            job_input_file = delayed_job_models.InputFile(internal_path=input_path)
            delayed_job_models.add_input_file_to_job(job, job_input_file)

    def simulate_outputs_of_job(self, job, output_dir):

        """
        Creates some output files and adds it to the job object
        :param job: job to add the output files to
        :param output_dir: directory where the job writes the outputs
        """
        outputs_path = os.path.join(output_dir, 'outputs')
        for i in range(1, 5):
            output_path = os.path.join(outputs_path, f'output{i}.txt')
            with open(outputs_path, 'w') as output_file:
                output_file.write(f'This is output {i}')

            job_output_file = delayed_job_models.OutputFile(internal_path=output_path)
            delayed_job_models.add_output_file_to_job(job, job_output_file)


    def simulate_finished_job(self, expires_at):
        """
        Creates a database a job that is finished. It will expire at the date passed as parameter.
        :param expires_at: Expiration date that you want for the job
        """

        # create a job
        job_type = delayed_job_models.JobTypes.SIMILARITY
        params = {
            'search_type': str(delayed_job_models.JobTypes.SIMILARITY),
            'structure': ''.join(random.choice(string.ascii_lowercase) for i in range(10)),
            'threshold': '70'
        }
        docker_image_url = 'some_url'

        job = delayed_job_models.get_or_create(job_type, params, docker_image_url)
        # simulate it finished

        job_run_dir = os.path.join(self.ABS_RUN_DIR_PATH, job.id)
        job.run_dir_path = job_run_dir
        os.makedirs(job_run_dir, exist_ok=True)

        output_dir = os.path.join(self.ABS_OUT_DIR_PATH, job.id)
        job.output_dir_path = output_dir
        os.makedirs(output_dir, exist_ok=True)
        print('output_dir: ', output_dir)

        # Add some inputs
        self.simulate_inputs_to_job(job, job_run_dir)

        # Add some outputs
        self.simulate_outputs_of_job(job, output_dir)

        job.status = delayed_job_models.JobStatuses.FINISHED
        job.expires_at = expires_at
        delayed_job_models.save_job(job)

        return job

    def test_deletes_expired_jobs(self):
        """
        Test that it deletes expired jobs correctly.
        """

        with self.flask_app.app_context():

            expired_time = datetime.datetime.utcnow() - datetime.timedelta(days=1)
            non_expired_time = datetime.datetime.utcnow() + datetime.timedelta(days=1)

            for time in [expired_time, non_expired_time]:
                self.simulate_finished_job(time)
                self.simulate_finished_job(time)

            num_deleted_got = delayed_job_models.delete_all_expired_jobs()
            current_time = datetime.datetime.utcnow()
            num_dirs_to_keep = 0
            for job in delayed_job_models.DelayedJob.query.all():
                expires_at_got = job.expires_at
                should_have_been_deleted = expires_at_got < current_time
                self.assertFalse(should_have_been_deleted,
                                 msg='The expired jobs were not deleted correctly')

                run_dir = job.run_dir_path
                self.assertTrue(os.path.exists(run_dir),
                                msg="The job run dir was deleted, it didn't expire!")

                out_dir = job.output_dir_path
                self.assertTrue(os.path.exists(out_dir),
                                msg="The job output dir was deleted, it didn't expire!")

                num_dirs_to_keep += 1

            num_run_dirs_got = len(os.listdir(self.ABS_RUN_DIR_PATH))
            self.assertEqual(num_run_dirs_got, num_dirs_to_keep, msg='Some expired run dirs were not deleted!')

            num_out_dirs_got = len(os.listdir(self.ABS_OUT_DIR_PATH))
            self.assertEqual(num_out_dirs_got, num_dirs_to_keep, msg='Some expired output dirs were not deleted!')

            num_deleted_must_be = 2
            self.assertEqual(num_deleted_must_be, num_deleted_got,
                             msg='The number of deleted jobs was not calculated correctly')
