"""
Tests for the job apis
"""
import json
import unittest
from app.authorisation import token_generator
from app import create_app
from app.apis.models import delayed_job_models
from app.db import db
import datetime
from pathlib import Path
import io
import os
import shutil


class TestStatus(unittest.TestCase):

    def setUp(self):
        self.flask_app = create_app()
        self.client = self.flask_app.test_client()

    def tearDown(self):

        with self.flask_app.app_context():
            delayed_job_models.delete_all_jobs()

    def test_get_existing_job_status(self):

        job_type = delayed_job_models.JobTypes.SIMILARITY
        params = {
            'search_type': str(delayed_job_models.JobTypes.SIMILARITY),
            'structure': '[H]C1(CCCN1C(=N)N)CC1=NC(=NO1)C1C=CC(=CC=1)NC1=NC(=CS1)C1C=CC(Br)=CC=1',
            'threshold': '70'
        }
        with self.flask_app.app_context():
            job_must_be = delayed_job_models.get_or_create(job_type, params)
            job_id = job_must_be.id

            client = self.client
            response = client.get(f'/status/{job_id}')
            resp_data = json.loads(response.data.decode('utf-8'))

            for property in ['type', 'status', 'status_comment', 'progress', 'created_at', 'started_at', 'finished_at',
                             'raw_params', 'expires_at', 'api_initial_url', 'timezone']:
                type_must_be = str(getattr(job_must_be, property))
                type_got = resp_data[property]
                self.assertEqual(type_must_be, type_got, msg=f'The returned job {property} is not correct.')

    def test_get_non_existing_job_status(self):

        client = self.client
        response = client.get('/status/some_id')
        self.assertEqual(response.status_code, 404, msg='A 404 not found error should have been produced')

    def test_a_job_cannot_update_another_job_status(self):

        job_type = delayed_job_models.JobTypes.SIMILARITY
        params = {
            'search_type': str(delayed_job_models.JobTypes.SIMILARITY),
            'structure': '[H]C1(CCCN1C(=N)N)CC1=NC(=NO1)C1C=CC(=CC=1)NC1=NC(=CS1)C1C=CC(Br)=CC=1',
            'threshold': '70'
        }

        with self.flask_app.app_context():

            job_must_be = delayed_job_models.get_or_create(job_type, params)
            job_id = job_must_be.id
            new_data = {
                'status': delayed_job_models.JobStatuses.RUNNING,
                'status_comment': 'Querying from web services',
                'progress': 50
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

        job_type = delayed_job_models.JobTypes.SIMILARITY
        params = {
            'search_type': str(delayed_job_models.JobTypes.SIMILARITY),
            'structure': '[H]C1(CCCN1C(=N)N)CC1=NC(=NO1)C1C=CC(=CC=1)NC1=NC(=CS1)C1C=CC(Br)=CC=1',
            'threshold': '70'
        }

        with self.flask_app.app_context():

            job_must_be = delayed_job_models.get_or_create(job_type, params)
            job_id = job_must_be.id
            new_data = {
                'status': delayed_job_models.JobStatuses.RUNNING,
                'status_comment': 'Querying from web services',
                'progress': 50
            }

            token = token_generator.generate_job_token(job_id)
            headers = {
                'X-JOB-KEY': token
            }
            client = self.client
            response = client.patch(f'/status/{job_id}', data=new_data, headers=headers)
            self.assertEqual(response.status_code, 200, msg='The request should have not failed')

            job_got = delayed_job_models.get_job_by_id(job_id)
            # be sure to have a fresh version of the object
            db.session.rollback()
            db.session.expire(job_got)
            db.session.refresh(job_got)

            for key, value_must_be in new_data.items():
                value_got = getattr(job_got, key)
                self.assertEqual(value_got, value_must_be, msg=f'The {key} was not updated correctly!')

    def test_started_at_time_is_calculated_correctly(self):

        job_type = delayed_job_models.JobTypes.SIMILARITY
        params = {
            'search_type': str(delayed_job_models.JobTypes.SIMILARITY),
            'structure': '[H]C1(CCCN1C(=N)N)CC1=NC(=NO1)C1C=CC(=CC=1)NC1=NC(=CS1)C1C=CC(Br)=CC=1',
            'threshold': '70'
        }

        with self.flask_app.app_context():
            job_must_be = delayed_job_models.get_or_create(job_type, params)
            job_id = job_must_be.id
            new_data = {
                'status': delayed_job_models.JobStatuses.RUNNING,
                'status_comment': 'Querying from web services',
                'progress': 50
            }

            token = token_generator.generate_job_token(job_id)
            headers = {
                'X-JOB-KEY': token
            }

            client = self.client
            response = client.patch(f'/status/{job_id}', data=new_data, headers=headers)
            started_at_time_must_be = datetime.datetime.utcnow().timestamp()
            self.assertEqual(response.status_code, 200, msg='The request should have not failed')

            job_got = delayed_job_models.get_job_by_id(job_id)
            # be sure to have a fresh version of the object
            db.session.rollback()
            db.session.expire(job_got)
            db.session.refresh(job_got)

            started_at_time_got = job_got.started_at.timestamp()
            self.assertAlmostEqual(started_at_time_must_be, started_at_time_got, places=1,
                                   msg='The started at time was not calculated correctly!')

    def test_finished_at_and_expires_time_are_calculated_correctly(self):
        job_type = delayed_job_models.JobTypes.SIMILARITY
        params = {
            'search_type': str(delayed_job_models.JobTypes.SIMILARITY),
            'structure': '[H]C1(CCCN1C(=N)N)CC1=NC(=NO1)C1C=CC(=CC=1)NC1=NC(=CS1)C1C=CC(Br)=CC=1',
            'threshold': '70'
        }

        with self.flask_app.app_context():
            job_must_be = delayed_job_models.get_or_create(job_type, params)
            job_id = job_must_be.id
            new_data = {
                'status': delayed_job_models.JobStatuses.FINISHED,
                'progress': 100
            }

            token = token_generator.generate_job_token(job_id)
            headers = {
                'X-JOB-KEY': token
            }

            client = self.client
            response = client.patch(f'/status/{job_id}', data=new_data, headers=headers)
            finished_at_time_must_be = datetime.datetime.utcnow().timestamp()
            expiration_time_must_be = (datetime.datetime.utcnow() +
                                       datetime.timedelta(days=delayed_job_models.DAYS_TO_LIVE)).timestamp()

            self.assertEqual(response.status_code, 200, msg='The request should have not failed')

            job_got = delayed_job_models.get_job_by_id(job_id)
            # be sure to have a fresh version of the object
            db.session.rollback()
            db.session.expire(job_got)
            db.session.refresh(job_got)

            finished_at_time_got = job_got.finished_at.timestamp()
            self.assertAlmostEqual(finished_at_time_must_be, finished_at_time_got, places=1,
                                   msg='The started at time was not calculated correctly!')

            expires_time_got = job_got.expires_at.timestamp()
            self.assertAlmostEqual(expiration_time_must_be, expires_time_got, places=1,
                                   msg='The expiration time was not calculated correctly!')

    def test_cannot_upload_file_to_non_existing_job(self):

        client = self.client
        response = client.post('/status/some_id/file', data={'results_file': (io.BytesIO(b"test"), 'test.txt')},
                               content_type='multipart/form-data')
        self.assertEqual(response.status_code, 404, msg='A 404 not found error should have been produced')

    def test_a_job_cannot_upload_files_for_another_job(self):

        job_type = delayed_job_models.JobTypes.SIMILARITY
        params = {
            'search_type': str(delayed_job_models.JobTypes.SIMILARITY),
            'structure': '[H]C1(CCCN1C(=N)N)CC1=NC(=NO1)C1C=CC(=CC=1)NC1=NC(=CS1)C1C=CC(Br)=CC=1',
            'threshold': '70'
        }

        with self.flask_app.app_context():

            job_must_be = delayed_job_models.get_or_create(job_type, params)
            client = self.client

            token = token_generator.generate_job_token('another_id')
            headers = {
                'X-JOB-KEY': token
            }

            response = client.post(f'/status/{job_must_be.id}/results_file',
                                   data={'file': (io.BytesIO(b"test"), 'test.txt')},
                                   content_type='multipart/form-data',
                                   headers=headers)

            self.assertEqual(response.status_code, 401,
                             msg='I should not be authorised to upload the file for another job')

    def test_a_job_results_file_is_uploaded(self):

        job_type = delayed_job_models.JobTypes.SIMILARITY
        params = {
            'search_type': str(delayed_job_models.JobTypes.SIMILARITY),
            'structure': '[H]C1(CCCN1C(=N)N)CC1=NC(=NO1)C1C=CC(=CC=1)NC1=NC(=CS1)C1C=CC(Br)=CC=1',
            'threshold': '70'
        }

        with self.flask_app.app_context():
            job_must_be = delayed_job_models.get_or_create(job_type, params)
            tmp_dir = os.path.join(str(Path().absolute()), 'tmp')
            output_dir_path = os.path.join(tmp_dir, job_must_be.id)
            os.makedirs(output_dir_path, exist_ok=True)
            job_must_be.output_dir_path = output_dir_path
            delayed_job_models.save_job(job_must_be)

            client = self.client

            token = token_generator.generate_job_token(job_must_be.id)
            headers = {
                'X-JOB-KEY': token
            }

            file_text = 'test'
            response = client.post(f'/status/{job_must_be.id}/results_file',
                                   data={'file': (io.BytesIO(f'{file_text}'.encode()), 'test.txt')},
                                   content_type='multipart/form-data',
                                   headers=headers)

            self.assertEqual(response.status_code, 200, msg='It was not possible to upload a job results file')
            # be sure to have a fresh version of the object
            db.session.rollback()
            db.session.expire(job_must_be)
            db.session.refresh(job_must_be)

            output_file_path_must_be = job_must_be.output_file_path
            with open(output_file_path_must_be, 'r') as file_got:
                self.assertEqual(file_got.read(), file_text, msg='Output file was not saved correctly')

            shutil.rmtree(tmp_dir)


    # TODO: test what chages after changing status to running, reporting to es, etc

