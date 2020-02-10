"""
Tests for the status namespace
"""
import datetime
import io
import json
import os
import shutil
import unittest
from pathlib import Path

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

        job_type = delayed_job_models.JobTypes.SIMILARITY
        params = {
            'search_type': str(delayed_job_models.JobTypes.SIMILARITY),
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
                         'raw_params', 'expires_at', 'api_initial_url', 'docker_image_url', 'timezone']:
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

        job_type = delayed_job_models.JobTypes.SIMILARITY
        params = {
            'search_type': str(delayed_job_models.JobTypes.SIMILARITY),
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

        job_type = delayed_job_models.JobTypes.SIMILARITY
        params = {
            'search_type': str(delayed_job_models.JobTypes.SIMILARITY),
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
            self.assertNotEqual(status_log_got, new_data['status_log'], msg=f'It seems that the status log was not saved '
                                                                         f'correctly. It should be accumulative')

            #
            # def test_started_at_time_is_calculated_correctly(self):
            #     """
            #     Tests that when the status is changed to running, the started_at time is calculated
            #     """
            #
            #     job_type = delayed_job_models.JobTypes.SIMILARITY
            #     params = {
            #         'search_type': str(delayed_job_models.JobTypes.SIMILARITY),
            #         'structure': '[H]C1(CCCN1C(=N)N)CC1=NC(=NO1)C1C=CC(=CC=1)NC1=NC(=CS1)C1C=CC(Br)=CC=1',
            #         'threshold': '70'
            #     }
            #
            #     with self.flask_app.app_context():
            #         job_must_be = delayed_job_models.get_or_create(job_type, params)
            #         job_id = job_must_be.id
            #         new_data = {
            #             'status': delayed_job_models.JobStatuses.RUNNING,
            #             'status_comment': 'Querying from web services',
            #             'progress': 50
            #         }
            #
            #         token = token_generator.generate_job_token(job_id)
            #         headers = {
            #             'X-JOB-KEY': token
            #         }
            #
            #         client = self.client
            #         response = client.patch(f'/status/{job_id}', data=new_data, headers=headers)
            #         started_at_time_must_be = datetime.datetime.utcnow().timestamp()
            #         self.assertEqual(response.status_code, 200, msg='The request should have not failed')
            #
            #         job_got = delayed_job_models.get_job_by_id(job_id)
            #         # be sure to have a fresh version of the object
            #         DB.session.rollback()
            #         DB.session.expire(job_got)
            #         DB.session.refresh(job_got)
            #
            #         started_at_time_got = job_got.started_at.timestamp()
            #         self.assertAlmostEqual(started_at_time_must_be, started_at_time_got, places=1,
            #                                msg='The started at time was not calculated correctly!')
            #
            # def test_finished_at_and_expires_time_are_calculated_correctly(self):
            #     """
            #     Tests that when a job status is set to FINISHED, the finished_at time, and expires_at time are calculated
            #     correctly
            #     """
            #     job_type = delayed_job_models.JobTypes.SIMILARITY
            #     params = {
            #         'search_type': str(delayed_job_models.JobTypes.SIMILARITY),
            #         'structure': '[H]C1(CCCN1C(=N)N)CC1=NC(=NO1)C1C=CC(=CC=1)NC1=NC(=CS1)C1C=CC(Br)=CC=1',
            #         'threshold': '70'
            #     }
            #
            #     with self.flask_app.app_context():
            #         job_must_be = delayed_job_models.get_or_create(job_type, params)
            #         job_id = job_must_be.id
            #         new_data = {
            #             'status': delayed_job_models.JobStatuses.FINISHED,
            #             'progress': 100
            #         }
            #
            #         token = token_generator.generate_job_token(job_id)
            #         headers = {
            #             'X-JOB-KEY': token
            #         }
            #
            #         client = self.client
            #         response = client.patch(f'/status/{job_id}', data=new_data, headers=headers)
            #         finished_at_time_must_be = datetime.datetime.utcnow().timestamp()
            #         expiration_time_must_be = (datetime.datetime.utcnow() +
            #                                    datetime.timedelta(days=delayed_job_models.DAYS_TO_LIVE)).timestamp()
            #
            #         self.assertEqual(response.status_code, 200, msg='The request should have not failed')
            #
            #         job_got = delayed_job_models.get_job_by_id(job_id)
            #         # be sure to have a fresh version of the object
            #         DB.session.rollback()
            #         DB.session.expire(job_got)
            #         DB.session.refresh(job_got)
            #
            #         finished_at_time_got = job_got.finished_at.timestamp()
            #         self.assertAlmostEqual(finished_at_time_must_be, finished_at_time_got, places=1,
            #                                msg='The started at time was not calculated correctly!')
            #
            #         expires_time_got = job_got.expires_at.timestamp()
            #         self.assertAlmostEqual(expiration_time_must_be, expires_time_got, places=1,
            #                                msg='The expiration time was not calculated correctly!')
            #
            # def test_cannot_upload_file_to_non_existing_job(self):
            #     """
            #     Tests that a file cannot be uploaded to a non existing job.
            #     """
            #
            #     client = self.client
            #     response = client.post('/status/some_id/file', data={'results_file': (io.BytesIO(b"test"), 'test.txt')},
            #                            content_type='multipart/form-data')
            #     self.assertEqual(response.status_code, 404, msg='A 404 not found error should have been produced')
            #
            # def test_a_job_cannot_upload_files_for_another_job(self):
            #     """
            #     Tests that a job cannot upload files for another job
            #     """
            #
            #     job_type = delayed_job_models.JobTypes.SIMILARITY
            #     params = {
            #         'search_type': str(delayed_job_models.JobTypes.SIMILARITY),
            #         'structure': '[H]C1(CCCN1C(=N)N)CC1=NC(=NO1)C1C=CC(=CC=1)NC1=NC(=CS1)C1C=CC(Br)=CC=1',
            #         'threshold': '70'
            #     }
            #
            #     with self.flask_app.app_context():
            #         job_must_be = delayed_job_models.get_or_create(job_type, params)
            #         client = self.client
            #
            #         token = token_generator.generate_job_token('another_id')
            #         headers = {
            #             'X-JOB-KEY': token
            #         }
            #
            #         response = client.post(f'/status/{job_must_be.id}/results_file',
            #                                data={'file': (io.BytesIO(b"test"), 'test.txt')},
            #                                content_type='multipart/form-data',
            #                                headers=headers)
            #
            #         self.assertEqual(response.status_code, 401,
            #                          msg='I should not be authorised to upload the file for another job')
            #
            # def test_a_job_results_file_is_uploaded(self):
            #     """
            #     Tests that a job can upload it's results file correctly.
            #     """
            #
            #     job_type = delayed_job_models.JobTypes.SIMILARITY
            #     params = {
            #         'search_type': str(delayed_job_models.JobTypes.SIMILARITY),
            #         'structure': '[H]C1(CCCN1C(=N)N)CC1=NC(=NO1)C1C=CC(=CC=1)NC1=NC(=CS1)C1C=CC(Br)=CC=1',
            #         'threshold': '70'
            #     }
            #
            #     with self.flask_app.app_context():
            #         job_must_be = delayed_job_models.get_or_create(job_type, params)
            #         tmp_dir = os.path.join(str(Path().absolute()), 'tmp')
            #         output_dir_path = os.path.join(tmp_dir, job_must_be.id)
            #         os.makedirs(output_dir_path, exist_ok=True)
            #         job_must_be.output_dir_path = output_dir_path
            #         delayed_job_models.save_job(job_must_be)
            #
            #         client = self.client
            #
            #         token = token_generator.generate_job_token(job_must_be.id)
            #         headers = {
            #             'X-JOB-KEY': token
            #         }
            #
            #         file_text = 'test'
            #         response = client.post(f'/status/{job_must_be.id}/results_file',
            #                                data={'file': (io.BytesIO(f'{file_text}'.encode()), 'test.txt')},
            #                                content_type='multipart/form-data',
            #                                headers=headers)
            #
            #         self.assertEqual(response.status_code, 200, msg='It was not possible to upload a job results file')
            #         # be sure to have a fresh version of the object
            #         DB.session.rollback()
            #         DB.session.expire(job_must_be)
            #         DB.session.refresh(job_must_be)
            #
            #         output_file_path_must_be = job_must_be.output_file_path
            #         with open(output_file_path_must_be, 'r') as file_got:
            #             self.assertEqual(file_got.read(), file_text, msg='Output file was not saved correctly')
            #
            #         shutil.rmtree(tmp_dir)
            #
            #         # pylint: disable=W0511
            #         # TODO: reporting to es, etc
