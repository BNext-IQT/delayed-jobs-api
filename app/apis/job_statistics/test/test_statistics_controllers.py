"""
Tests for the search statistics API
"""
import unittest
from app import create_app
from app.db import db
from app.apis.models import delayed_job_models
from app.authorisation import token_generator
import datetime
import json


class TestStatus(unittest.TestCase):

    def setUp(self):
        self.flask_app = create_app()
        self.client = self.flask_app.test_client()

    def tearDown(self):

        with self.flask_app.app_context():
            delayed_job_models.delete_all_jobs()

    def test_cannot_save_statistics_with_invalid_token(self):

        with self.flask_app.app_context():
            statistics = {
                'total_items': 100,
                'file_size': 100
            }

            token = token_generator.generate_job_token('another_id')
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

            token = token_generator.generate_job_token('some_job_id')
            headers = {
                'X-JOB-KEY': token
            }

            client = self.client
            response = client.post('record/search/some_job_id', data=statistics, headers=headers)

            self.assertEqual(response.status_code, 404,
                             msg='I should not be able to save statistics for a job that does not exist')

    def test_job_must_be_finished_to_save_statistics(self):

        with self.flask_app.app_context():

            job_type = delayed_job_models.JobTypes.SIMILARITY
            params = {
                'search_type': str(delayed_job_models.JobTypes.SIMILARITY),
                'structure': '[H]C1(CCCN1C(=N)N)CC1=NC(=NO1)C1C=CC(=CC=1)NC1=NC(=CS1)C1C=CC(Br)=CC=1',
                'threshold': '70'
            }

            with self.flask_app.app_context():

                job_must_be = delayed_job_models.get_or_create(job_type, params)

                statistics = {
                    'total_items': 100,
                    'file_size': 100
                }

                token = token_generator.generate_job_token(job_must_be.id)
                headers = {
                    'X-JOB-KEY': token
                }

                client = self.client
                response = client.post(f'record/search/{job_must_be.id}', data=statistics, headers=headers)
                self.assertEqual(response.status_code, 412, msg='The job must be finished before saving statistics')

    def test_saves_statistics_for_search_job(self):

        with self.flask_app.app_context():

            job_type = delayed_job_models.JobTypes.SIMILARITY
            params = {
                'search_type': str(delayed_job_models.JobTypes.SIMILARITY),
                'structure': '[H]C1(CCCN1C(=N)N)CC1=NC(=NO1)C1C=CC(=CC=1)NC1=NC(=CS1)C1C=CC(Br)=CC=1',
                'threshold': '70'
            }

            with self.flask_app.app_context():

                time_taken_must_be = 10
                job_must_be = delayed_job_models.get_or_create(job_type, params)
                job_must_be.started_at = datetime.datetime.utcnow()
                job_must_be.finished_at = job_must_be.started_at + datetime.timedelta(seconds=time_taken_must_be)

                job_must_be.status = delayed_job_models.JobStatuses.FINISHED
                db.session.commit()

                statistics = {
                    'total_items': 100,
                    'file_size': 100
                }

                token = token_generator.generate_job_token(job_must_be.id)
                headers = {
                    'X-JOB-KEY': token
                }

                client = self.client
                response = client.post(f'record/search/{job_must_be.id}', data=statistics, headers=headers)

                data_got = json.loads(response.data.decode('UTF-8'))
                time_taken_got = data_got.get('time_taken')
                self.assertEqual(time_taken_got, time_taken_must_be, msg='The time taken was not calculated correctly')

                search_type_must_be = str(job_must_be.type)
                search_type_got = data_got.get('search_type')
                self.assertEqual(search_type_must_be, search_type_got,
                                 msg='The search type is wrong!')

                request_date_must_be = job_must_be.created_at.timestamp()
                request_date_got = data_got.get('request_date')
                self.assertAlmostEqual(request_date_must_be, request_date_got, places=1,
                                 msg='The request date was not calculated correctly')