"""
Tests for the status namespace
"""
import json
import unittest

from app import create_app
from app.authorisation import token_generator
from app.db import DB
from app.models import delayed_job_models


# pylint: disable=E1101
class TestStatus(unittest.TestCase):
    """
    Class that tests the status namespace
    """

    def setUp(self):
        self.flask_app = create_app()
        self.client = self.flask_app.test_client()

    def tearDown(self):
        with self.flask_app.app_context():
            delayed_job_models.delete_all_jobs()

    def test_get_existing_job_status(self):
        """
        Tests that the status of an existing job is returned correctly.
        """

        job_type = 'SIMILARITY'
        params = {
            'search_type': 'SIMILARITY',
            'structure': '[H]C1(CCCN1C(=N)N)CC1=NC(=NO1)C1C=CC(=CC=1)NC1=NC(=CS1)C1C=CC(Br)=CC=1',
            'threshold': '70'
        }
        docker_image_url = 'some url'

        with self.flask_app.app_context():
            job_must_be = delayed_job_models.get_or_create(job_type, params, docker_image_url)
            job_id = job_must_be.id

            client = self.client
            response = client.get(f'/status/{job_id}')
            resp_data = json.loads(response.data.decode('utf-8'))

            for prop in ['type', 'status', 'status_log', 'progress', 'created_at', 'started_at', 'finished_at',
                         'raw_params', 'expires_at', 'api_initial_url', 'docker_image_url', 'timezone', 'num_failures',
                         'status_description']:
                type_must_be = str(getattr(job_must_be, prop))
                type_got = resp_data[prop]
                self.assertEqual(type_must_be, type_got, msg=f'The returned job {prop} is not correct.')

    def test_get_non_existing_job_status(self):
        """
        Tests that when the status of a non existing job a 404 error is produced.
        """

        client = self.client
        response = client.get('/status/some_id')
        self.assertEqual(response.status_code, 404, msg='A 404 not found error should have been produced')

    def test_a_job_cannot_update_another_job_progress(self):
        """
        Tests that a job can not use its token to update another job's status
        """

        job_type = 'SIMILARITY'
        params = {
            'search_type': 'SIMILARITY',
            'structure': '[H]C1(CCCN1C(=N)N)CC1=NC(=NO1)C1C=CC(=CC=1)NC1=NC(=CS1)C1C=CC(Br)=CC=1',
            'threshold': '70'
        }
        docker_image_url = 'some url'

        with self.flask_app.app_context():
            job_must_be = delayed_job_models.get_or_create(job_type, params, docker_image_url)
            job_id = job_must_be.id
            new_data = {
                'progress': 50,
                'status_log': 'Loading database',
            }

            token = token_generator.generate_job_token('another_id')
            headers = {
                'X-JOB-KEY': token
            }
            client = self.client
            response = client.patch(f'/status/{job_id}', data=new_data, headers=headers)

            self.assertEqual(response.status_code, 401,
                             msg='I should not be authorised to modify the status of another job')

    def test_update_job_status(self):
        """
        Tests that a job can update its status
        """

        job_type = 'SIMILARITY'
        params = {
            'search_type': 'SIMILARITY',
            'structure': '[H]C1(CCCN1C(=N)N)CC1=NC(=NO1)C1C=CC(=CC=1)NC1=NC(=CS1)C1C=CC(Br)=CC=1',
            'threshold': '70'
        }
        docker_image_url = 'some url'

        with self.flask_app.app_context():
            job_must_be = delayed_job_models.get_or_create(job_type, params, docker_image_url)
            job_id = job_must_be.id
            new_data = {
                'progress': 50,
                'status_log': 'Loading database',
                'status_description': '{"msg":"Smiles file loaded"}'
            }

            token = token_generator.generate_job_token(job_id)
            headers = {
                'X-Job-Key': token
            }

            client = self.client
            response = client.patch(f'/status/{job_id}', data=new_data, headers=headers)
            self.assertEqual(response.status_code, 200, msg='The request should have not failed')

            job_got = delayed_job_models.get_job_by_id(job_id)
            # be sure to have a fresh version of the object
            DB.session.rollback()
            DB.session.expire(job_got)
            DB.session.refresh(job_got)

            progress_got = job_got.progress
            self.assertEqual(progress_got, new_data['progress'], msg=f'The progress was not updated correctly!')

            status_log_got = job_got.status_log
            self.assertIsNotNone(status_log_got, msg=f'The status log was not set correctly!')
            self.assertNotEqual(status_log_got, new_data['status_log'],
                                msg=f'It seems that the status log was not saved'
                                    f'correctly. It should be accumulative')

            status_description_got = job_got.status_description
            self.assertEqual(status_description_got, new_data['status_description'],
                             msg=f'The status description was not updated correctly!')

    def test_update_job_status_no_status_log(self):
        """
        Tests that a job can update its status without providing a status log
        """

        job_type = 'SIMILARITY'
        params = {
            'search_type': 'SIMILARITY',
            'structure': '[H]C1(CCCN1C(=N)N)CC1=NC(=NO1)C1C=CC(=CC=1)NC1=NC(=CS1)C1C=CC(Br)=CC=1',
            'threshold': '70'
        }
        docker_image_url = 'some url'

        with self.flask_app.app_context():
            job_must_be = delayed_job_models.get_or_create(job_type, params, docker_image_url)
            job_id = job_must_be.id
            new_data = {
                'progress': 50,

            }

            token = token_generator.generate_job_token(job_id)
            headers = {
                'X-Job-Key': token
            }

            client = self.client
            response = client.patch(f'/status/{job_id}', data=new_data, headers=headers)
            self.assertEqual(response.status_code, 200, msg='The request should have not failed')

            job_got = delayed_job_models.get_job_by_id(job_id)
            # be sure to have a fresh version of the object
            DB.session.rollback()
            DB.session.expire(job_got)
            DB.session.refresh(job_got)

            progress_got = job_got.progress
            self.assertEqual(progress_got, new_data['progress'], msg=f'The progress was not updated correctly!')

            status_log_got = job_got.status_log
            self.assertIsNone(status_log_got, msg=f'The status should have not been modified!')
