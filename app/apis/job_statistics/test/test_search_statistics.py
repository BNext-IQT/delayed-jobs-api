"""
Tests for the search statistics API
"""
import unittest
from app import create_app
from app.db import db
from app.apis.models import delayed_job_models
from app.apis.job_submission import job_submission_service


class TestStatus(unittest.TestCase):

    def setUp(self):
        self.flask_app = create_app()
        self.client = self.flask_app.test_client()

        with self.flask_app.app_context():
            db.create_all()

    def tearDown(self):

        with self.flask_app.app_context():
            delayed_job_models.delete_all_jobs()

    def test_cannot_save_statistics_with_invalid_token(self):

        with self.flask_app.app_context():
            statistics = {
                'total_items': 100,
                'file_size': 100
            }

            token = job_submission_service.generate_job_token('another_id')
            headers = {
                'X-JOB-KEY': token
            }

            client = self.client
            response = client.post('record/search/some_job_id', data=statistics, headers=headers)
            self.assertEqual(response.status_code, 401,
                             msg='I should not be authorised to save statistics for a job with an invalid token')

    def test_job_id_must_exist(self):
        """
        Tests that a job id must exist when saving statistics for it
        :return:
        """

        with self.flask_app.app_context():
            statistics = {
                'total_items': 100,
                'file_size': 100
            }

            token = job_submission_service.generate_job_token('some_job_id')
            headers = {
                'X-JOB-KEY': token
            }

            client = self.client
            response = client.post('record/search/some_job_id', data=statistics, headers=headers)

            self.assertEqual(response.status_code, 404,
                             msg='I should not be able to save statistics for a job that does not exist')