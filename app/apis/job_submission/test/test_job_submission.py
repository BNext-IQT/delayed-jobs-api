"""
This module tests jobs submission to the EBI queue
"""
import unittest
import jwt
from app.config import RUN_CONFIG
from app.apis.job_submission import job_submission_service
from app.apis.models import delayed_job_models
from app import create_app
import os
import yaml
from app.authorisation import token_generator


class TestJobSubmitter(unittest.TestCase):
    """
    Class to test job submission
    """

    def setUp(self):
        self.flask_app = create_app()
        self.client = self.flask_app.test_client()

    def tearDown(self):

        with self.flask_app.app_context():
            delayed_job_models.delete_all_jobs()

    def test_job_token_is_generated(self):
        """
            Test that the token for a job is generated
        """
        with self.flask_app.app_context():
            job_type = delayed_job_models.JobTypes.SIMILARITY
            params = {
                'structure': '[H]C1(CCCN1C(=N)N)CC1=NC(=NO1)C1C=CC(=CC=1)NC1=NC(=CS1)C1C=CC(Br)=CC=1',
                'threshold': '70'
            }
            job_must_be = delayed_job_models.get_or_create(job_type, params)
            token_got = token_generator.generate_job_token(job_must_be.id)
            key = RUN_CONFIG.get('server_secret_key')
            data_got = jwt.decode(token_got, key, algorithms=['HS256'])
            self.assertEqual(data_got.get('job_id'), job_must_be.id, msg='The token was not generated correctly!')


    # pylint: disable=no-self-use
    def test_job_can_be_submitted(self):
        """
        Test that a job can be submitted
        """
        with self.flask_app.app_context():
            job_type = delayed_job_models.JobTypes.SIMILARITY
            params = {
                'structure': '[H]C1(CCCN1C(=N)N)CC1=NC(=NO1)C1C=CC(=CC=1)NC1=NC(=CS1)C1C=CC(Br)=CC=1',
                'threshold': '70'
            }
            job_data = job_submission_service.submit_job(job_type, params)
            job_id = job_data.get('id')

            job_run_dir_must_be = os.path.join(job_submission_service.JOBS_RUN_DIR, job_id)
            self.assertTrue(os.path.isdir(job_run_dir_must_be),
                            msg=f'The run dir for the job ({job_run_dir_must_be}) has not been created!')

            params_file_must_be = os.path.join(job_run_dir_must_be, job_submission_service.RUN_PARAMS_FILENAME)

            self.assertTrue(os.path.isfile(params_file_must_be),
                            msg=f'The run params file for the job ({params_file_must_be}) has not been created!')

            params_file = open(params_file_must_be, 'r')
            params_got = yaml.load(params_file, Loader=yaml.FullLoader)
            params_file.close()

            token_must_be = token_generator.generate_job_token(job_id)
            token_got = params_got.get('job_token')
            self.assertEqual(token_must_be, token_got, msg='The token was not generated correctly')

            job_id_must_be = job_id
            job_id_got = params_got.get('job_id')
            self.assertEqual(job_id_must_be, job_id_got, msg='The job id was not generated correctly')

            # See how this works when deploying, one option could be to use the client?
            status_update_url_must_be = f'http://127.0.0.1:5000/status/{job_id}'
            status_update_url_got = params_got.get('status_update_endpoint').get('url')
            self.assertEqual(status_update_url_must_be, status_update_url_got,
                             msg='The status update url was not set correctly!')

            status_update_method_must_be = 'PATCH'
            status_update_method_got = params_got.get('status_update_endpoint').get('method')
            self.assertEqual(status_update_method_must_be, status_update_method_got,
                             msg='The status update method was not set correctly!')

            statistics_url_must_be = f'http://127.0.0.1:5000/record/search/{job_id}'
            statistics_url_got = params_got.get('statistics_endpoint').get('url')
            self.assertEqual(statistics_url_must_be, statistics_url_got,
                             msg='The statistics url was not set correctly!')

            statistics_method_must_be = 'POST'
            statistics_method_got = params_got.get('statistics_endpoint').get('method')
            self.assertEqual(statistics_method_must_be, statistics_method_got,
                             msg='The statistics update method was not set correctly!')

            job_params_got = params_got.get('job_params')
            job_params_must_be = job_data.get('raw_params')
            self.assertEqual(job_params_got, job_params_must_be,
                             msg='The job params were not set correctly')

            script_file_must_be = \
                os.path.join(job_run_dir_must_be, job_submission_service.SCRIPT_FILENAMES.get(job_data.get('type')))

            self.assertTrue(os.path.isfile(script_file_must_be),
                            msg=f'The script file for the job ({script_file_must_be}) has not been created!')

            self.assertTrue(os.access(script_file_must_be, os.X_OK),
                            msg=f'The script file for the job ({script_file_must_be}) is not executable!')



