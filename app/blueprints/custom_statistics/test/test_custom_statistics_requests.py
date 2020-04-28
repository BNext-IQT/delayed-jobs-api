"""
Tests for the custom statistics blueprint
"""
import unittest

from app import create_app
from app.models import delayed_job_models
from app.authorisation import token_generator


class TestCustomStatistics(unittest.TestCase):
    """
    Class to test the custom statistics endpoints
    """
    def setUp(self):
        self.flask_app = create_app()
        self.client = self.flask_app.test_client()

    def tearDown(self):
        with self.flask_app.app_context():
            delayed_job_models.delete_all_jobs()

    def test_a_job_cannot_update_another_jobs_statistics(self):
        """
        Tests that a job cannot update the statistics of another job
        """
        job_type = 'TEST'
        params = {
            'instruction': 'RUN_NORMALLY',
            'seconds': 1,
            'api_url': 'https://www.ebi.ac.uk/chembl/api/data/similarity/CN1C(=O)C=C(c2cccc(Cl)c2)c3cc(ccc13)C@@(c4ccc(Cl)cc4)c5cncn5C/80.json'
        }
        docker_image_url = 'some url'

        with self.flask_app.app_context():
            job_must_be = delayed_job_models.get_or_create(job_type, params, docker_image_url)
            job_id = job_must_be.id
            statistics = {
                'duration': 1,
            }

            token = token_generator.generate_job_token('another_id')
            headers = {
                'X-JOB-KEY': token
            }
            client = self.client
            response = client.post(f'/custom_statistics/submit_statistics/test_job/{job_id}',
                                   data=statistics, headers=headers)

            self.assertEqual(response.status_code, 401,
                             msg='I should not be authorised to upload statistics of another job')
