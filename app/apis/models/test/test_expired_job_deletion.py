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
from app.apis.models import delayed_job_models


class TestModels(unittest.TestCase):

    TEST_RUN_DIR_NAME = 'test_run_dir'
    ABS_RUN_DIR_PATH = str(Path(TEST_RUN_DIR_NAME).resolve())

    def setUp(self):
        self.flask_app = create_app()
        self.client = self.flask_app.test_client()

        os.makedirs(self.ABS_RUN_DIR_PATH, exist_ok=True)

    def tearDown(self):

        with self.flask_app.app_context():
            delayed_job_models.delete_all_jobs()

        shutil.rmtree(self.ABS_RUN_DIR_PATH)

    def simulate_finished_job(self, expires_at):

        # create a job
        job_type = delayed_job_models.JobTypes.SIMILARITY
        params = {
            'search_type': str(delayed_job_models.JobTypes.SIMILARITY),
            'structure': ''.join(random.choice(string.ascii_lowercase) for i in range(10)),
            'threshold': '70'
        }

        job = delayed_job_models.get_or_create(job_type, params)
        # simulate it finished

        job_run_dir = os.path.join(self.ABS_RUN_DIR_PATH, job.id)
        job.run_dir_path = job_run_dir
        os.makedirs(job_run_dir, exist_ok=True)

        job_execution = delayed_job_models.JobExecution(
            hostname='hostname',
            command='some_command',
            pid='123',
            run_dir=str(job_run_dir)
        )
        delayed_job_models.add_job_execution_to_job(job, job_execution)
        job.status = delayed_job_models.JobStatuses.FINISHED
        job.expires_at = expires_at
        delayed_job_models.save_job(job)

        return job

    def test_deletes_expired_jobs(self):

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

                num_dirs_to_keep += 1

            num_dirs_got = len(os.listdir(self.ABS_RUN_DIR_PATH))
            self.assertEqual(num_dirs_got, num_dirs_to_keep, msg='Some expired run dirs were not deleted!')

            num_deleted_must_be = 2
            self.assertEqual(num_deleted_must_be, num_deleted_got,
                             msg='The number of deleted jobs was not calculated correctly')
