"""
This module tests jobs submission to the EBI queue
"""
import json
import os
import random
import shutil
import unittest
from pathlib import Path

import jwt
import yaml

from app import create_app
from app.authorisation import token_generator
from app.config import RUN_CONFIG
from app.models import delayed_job_models
from app.blueprints.job_submission.services import job_submission_service


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
            jobs_run_dir = job_submission_service.JOBS_RUN_DIR
            jobs_tmp_dir = job_submission_service.JOBS_TMP_DIR
            jobs_out_dir = job_submission_service.JOBS_OUTPUT_DIR

            try:
                shutil.rmtree(jobs_run_dir)
                shutil.rmtree(jobs_tmp_dir)
                shutil.rmtree(jobs_out_dir)
            except FileNotFoundError:
                pass

    def test_job_token_is_generated(self):
        """
            Test that the token for a job is generated
        """
        with self.flask_app.app_context():
            job_type = delayed_job_models.JobTypes.SIMILARITY
            params = {
                'search_type': str(delayed_job_models.JobTypes.SIMILARITY),
                'structure': '[H]C1(CCCN1C(=N)N)CC1=NC(=NO1)C1C=CC(=CC=1)NC1=NC(=CS1)C1C=CC(Br)=CC=1',
                'threshold': '70'
            }
            docker_image_url = 'some_url'
            job_must_be = delayed_job_models.get_or_create(job_type, params, docker_image_url)
            token_got = token_generator.generate_job_token(job_must_be.id)
            key = RUN_CONFIG.get('server_secret_key')
            data_got = jwt.decode(token_got, key, algorithms=['HS256'])
            self.assertEqual(data_got.get('job_id'), job_must_be.id, msg='The token was not generated correctly!')

    def prepare_mock_job_args(self):
        """
        Creates some mock input files and returns some parameters as they will be used by the job submission function
        :return: a tuple with the mock input files description, input files hashes, and job params
        """

        tmp_dir = Path(job_submission_service.JOBS_TMP_DIR).joinpath(f'{random.randint(1, 1000000)}')
        os.makedirs(tmp_dir, exist_ok=True)

        input_files_desc = {
            'input1': str(Path.joinpath(tmp_dir, 'input1.txt')),
            'input2': str(Path.joinpath(tmp_dir, 'input2.txt'))
        }

        for key, path in input_files_desc.items():
            with open(path, 'w') as input_file:
                input_file.write(f'This is input file {key}')

        input_files_hashes = {
            'input1': 'hash1-hash1-hash1-hash1-hash1-hash1-hash1',
            'input2': 'hash2-hash2-hash2-hash2-hash2-hash2-hash2',
        }

        params = {
            'instruction': 'RUN_NORMALLY',
            'seconds': 1,
            'api_url': 'https://www.ebi.ac.uk/chembl/api/data/similarity/CN1C(=O)C=C(c2cccc(Cl)c2)c3cc(ccc13)[C@@](N)(c4ccc(Cl)cc4)c5cncn5C/80.json'
        }

        return input_files_desc, input_files_hashes, params

    # pylint: disable=no-self-use
    # pylint: disable=too-many-locals
    def test_job_can_be_submitted(self):
        """
        Test that a job can be submitted
        """
        with self.flask_app.app_context():
            job_type = delayed_job_models.JobTypes.TEST
            docker_image_url = 'some_url'

            input_files_desc, input_files_hashes, params = self.prepare_mock_job_args()
            submission_result = job_submission_service.submit_job(job_type, input_files_desc, input_files_hashes,
                                                         docker_image_url, params)

            job_id = submission_result.get('job_id')
            job_data = delayed_job_models.get_job_by_id(job_id).public_dict()
            # -----------------------------------------------
            # Test Run Dir
            # -----------------------------------------------
            job_run_dir_must_be = os.path.join(job_submission_service.JOBS_RUN_DIR, job_id)
            self.assertTrue(os.path.isdir(job_run_dir_must_be),
                            msg=f'The run dir for the job ({job_run_dir_must_be}) has not been created!')

            input_files_dir_must_be = os.path.join(job_run_dir_must_be, job_submission_service.INPUT_FILES_DIR_NAME)
            self.assertTrue(os.path.isdir(input_files_dir_must_be),
                            msg=f'The input files dir for the job ({input_files_dir_must_be}) has not been created!')

            # -----------------------------------------------
            # Test Run Params
            # -----------------------------------------------
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

            status_update_url_must_be = f'http://0.0.0.0:5000/status/{job_id}'
            status_update_url_got = params_got.get('status_update_endpoint').get('url')
            self.assertEqual(status_update_url_must_be, status_update_url_got,
                             msg='The status update url was not set correctly!')

            status_update_method_must_be = 'PATCH'
            status_update_method_got = params_got.get('status_update_endpoint').get('method')
            self.assertEqual(status_update_method_must_be, status_update_method_got,
                             msg='The status update method was not set correctly!')

            job_params_got = params_got.get('job_params')
            print('job_params_got: ', job_params_got)

            raw_job_params_must_be = job_data.get('raw_params')
            print('raw_job_params_must_be: ', raw_job_params_must_be)
            self.assertEqual(json.dumps(job_params_got, sort_keys=True), raw_job_params_must_be,
                             msg='The job params were not set correctly')

            # -----------------------------------------------
            # Test Input Files
            # -----------------------------------------------
            job_input_files_desc_got = params_got.get('inputs')
            for key, tmp_path in input_files_desc.items():
                run_path_must_be = job_input_files_desc_got[key]
                self.assertTrue(os.path.isfile(run_path_must_be),
                                msg=f'The input file for the job ({run_path_must_be}) has not been created!')

            # -----------------------------------------------
            # Test Output Directory
            # -----------------------------------------------
            output_dir_must_be = Path(job_submission_service.JOBS_OUTPUT_DIR).joinpath(job_id)
            output_dir_got = params_got.get('output_dir')
            self.assertEqual(str(output_dir_got), str(output_dir_must_be),
                             msg='The job output dir was not set correctly')
            self.assertTrue(os.path.isdir(output_dir_must_be),
                            msg=f'The output dir for the job ({output_dir_must_be}) has not been created!')

            # -----------------------------------------------
            # Submission script file
            # -----------------------------------------------
            submission_script_file_must_be = \
                os.path.join(job_run_dir_must_be, job_submission_service.SUBMISSION_FILE_NAME)

            self.assertTrue(os.path.isfile(submission_script_file_must_be),
                            msg=f'The script file for submitting the job ({submission_script_file_must_be}) '
                                f'has not been created!')

            self.assertTrue(os.access(submission_script_file_must_be, os.X_OK),
                            msg=f'The script file for the job ({submission_script_file_must_be}) is not executable!')
