"""
Tests for the deletion of job outputs
"""
import unittest
from pathlib import Path
import os
import shutil

from app import create_app
from app.blueprints.admin.controllers.test import utils
from app.models import delayed_job_models
from app.blueprints.admin.services import admin_tasks_service

class TestJobOutputDeletion(unittest.TestCase):
    """
    Class to test the deletion of the outputs of jobs
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

    def test_deletes_output_of_job(self):
        """
        Tests that it deletes the output that a job created
        """
        with self.flask_app.app_context():
            job = utils.simulate_finished_job(self.ABS_RUN_DIR_PATH)

            admin_tasks_service.delete_all_outputs_of_job(job.id)
            num_items_got = len(os.listdir(job.output_dir_path))

            self.assertEqual(num_items_got, 0, msg='The outputs were not deleted correctly!')





