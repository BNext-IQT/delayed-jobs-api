"""
Tests for the job apis
"""
import json
import unittest

from app import create_app
from app.apis.models import delayed_job_models
from app.db import db


class TestStatus(unittest.TestCase):

    def setUp(self):
        self.flask_app = create_app()
        self.client = self.flask_app.test_client()

        with self.flask_app.app_context():
            db.create_all()

    def test_get_existing_job_status(self):

        job_type = delayed_job_models.JobTypes.SIMILARITY
        params = {
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
                             'output_file_path', 'raw_params', 'expires', 'api_initial_url', 'timezone']:
                type_must_be = str(getattr(job_must_be, property))
                type_got = resp_data[property]
                self.assertEqual(type_must_be, type_got, msg=f'The returned job {property} is not correct.')

    def test_get_non_existing_job_status(self):

        client = self.client
        response = client.get(f'/status/some_id')
        self.assertEqual(response.status_code, 400, msg='A 404 not found error should have been produced')

    def test_update_job_status(self):

        job_type = delayed_job_models.JobTypes.SIMILARITY
        params = {
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

            client = self.client
            response = client.patch(f'/status/{job_id}', data=new_data)
            self.assertEqual(response.status_code, 200, msg='The request should have not failed')

            job_got = delayed_job_models.get_job_by_id(job_id)
            # be sure to have a fresh version of the object
            db.session.rollback()
            db.session.expire(job_got)
            db.session.refresh(job_got)

            for key, value_must_be in new_data.items():
                value_got = getattr(job_got, key)
                self.assertEqual(value_got, value_must_be, msg=f'The {key} was not updated correctly!')
                

    # TODO: test what chages after changing status to running, reporting to es, etc

