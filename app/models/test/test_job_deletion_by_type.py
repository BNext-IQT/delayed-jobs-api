"""
Tests for deleting jobs of a certain type
"""
import unittest
from pathlib import Path
import os
import shutil
import random
import string

from app import create_app
from app.models import delayed_job_models
from app.models.test import utils


class TestJobDeletionByType(unittest.TestCase):
    """
    Class to test deletion of jobs by a given type
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

    def simulate_finished_job_of_a_type(self, job_type):
        """
        Creates a database a job that is finished. It will be of the type given as parameter.
        There will be some randomness in the parameters to generate some random ids
        :param type: type that you want the job to be
        """

        params = {
            'structure': ''.join(random.choice(string.ascii_lowercase) for i in range(10)),
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

        # Add some inputs
        utils.simulate_inputs_to_job(job, job_run_dir)

        # Add some outputs
        utils.simulate_outputs_of_job(job, output_dir)

        job.status = delayed_job_models.JobStatuses.FINISHED
        delayed_job_models.save_job(job)

        return job


    def test_deletes_all_jobs_of_a_given_type(self):
        """
        Tests that the operation of deleting a job of a certain type is executed correctly.
        """

        with self.flask_app.app_context():

            type_to_delete = 'FOR_DELETION'
            type_to_not_delete = 'DO_NOT_DELETE'
            job_per_type = 6

            for job_type in [type_to_delete, type_to_not_delete]:
                for i in range(0, job_per_type):
                    self.simulate_finished_job_of_a_type(job_type)

            num_deleted_got = delayed_job_models.delete_all_jobs_by_type(type_to_delete)
            self.assertEqual(job_per_type, num_deleted_got, msg='The correct amount of jobs was not deleted!')

            num_dirs_to_keep = 0
            for job in delayed_job_models.DelayedJob.query.all():
                should_have_been_deleted = job.type == type_to_delete
                self.assertFalse(should_have_been_deleted,
                                 msg='A job was not deleted correctly')

                run_dir = job.run_dir_path
                self.assertTrue(os.path.exists(run_dir),
                                msg="The job run dir was deleted, it didn't expire!")

                out_dir = job.output_dir_path
                self.assertTrue(os.path.exists(out_dir),
                                msg="The job output dir was deleted, it didn't expire!")

                num_dirs_to_keep += 1

            num_run_dirs_got = len(os.listdir(self.ABS_RUN_DIR_PATH))
            self.assertEqual(num_run_dirs_got, num_dirs_to_keep, msg='Some run dirs were not deleted!')

            num_out_dirs_got = len(os.listdir(self.ABS_OUT_DIR_PATH))
            self.assertEqual(num_out_dirs_got, num_dirs_to_keep, msg='Some output dirs were not deleted!')

