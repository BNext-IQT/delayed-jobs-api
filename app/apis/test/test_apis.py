"""
Tests for the job apis
"""
import unittest
from app import create_app
from app.models import delayed_job_models
from app.models.db import db
import json


class TestStatus(unittest.TestCase):

    def setUp(self):
        self.flask_app = create_app()
        self.client = self.flask_app.test_client()

        with self.flask_app.app_context():
            db.create_all()

    def test_get_existing_job_status(self):

        # set up an a job in the database
        job_type = delayed_job_models.JobTypes.SIMILARITY
        params = {
            'structure': '[H]C1(CCCN1C(=N)N)CC1=NC(=NO1)C1C=CC(=CC=1)NC1=NC(=CS1)C1C=CC(Br)=CC=1',
            'threshold': '70'
        }
        with self.flask_app.app_context():
            job_must_be = delayed_job_models.get_or_create(job_type, params)
            job_id = job_must_be.id
            # set up an a job in the database

            client = self.client
            response = client.get(f'/status/{job_id}')
            resp_data = json.loads(response.data.decode('utf-8'))

            for property in ['type', 'status', 'status_comment', 'progress', 'created_at', 'started_at', 'finished_at',
                             'output_file_path', 'raw_params', 'expires', 'api_initial_url', 'timezone']:
                type_must_be = str(getattr(job_must_be, property))
                type_got = resp_data[property]
                self.assertEqual(type_must_be, type_got, msg=f'The returned job {property} is not correct.')


