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
from app.db import DB


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
            job_type = 'SIMILARITY'
            params = {
                'search_type': 'SIMILARITY',
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
            job_type = 'TEST'
            docker_image_url = 'some_url'

            input_files_desc, input_files_hashes, params = self.prepare_mock_job_args()
            print('TEST INPUT ')
            print(input_files_desc)
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
            raw_job_params_must_be = job_data.get('raw_params')
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

            # DB.session.commit()
            # DB.session.expire_all()
            job_got = delayed_job_models.get_job_by_id(job_id)
            input_files_got = job_got.input_files
            num_inputs_files_must_be = len(os.listdir(input_files_dir_must_be))
            self.assertEquals(num_inputs_files_must_be, len(input_files_got),
                              msg='The input files were not registered correctly!')

            for input_file in input_files_got:
                internal_path_got = input_file.internal_path
                self.assertTrue(os.path.isfile(internal_path_got),
                                msg=f'The internal path of an input file {internal_path_got} '
                                    f'seems that does not exist!')

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

    def test_lsf_job_id_is_parsed_correctly_after_submission(self):

        lsf_id_must_be = 2010993
        sample_output = f'I am going to submit the job TEST-QGtXZZhmNOfL2BYyvOuZ5JKhz06MEL8oU8wGwgNOYQA=\n' \
                        f'Job <{lsf_id_must_be}> is submitted to default queue <normal>.\n'

        lsf_job_id_got = job_submission_service.get_lsf_job_id(sample_output)
        self.assertEqual(lsf_id_must_be, lsf_job_id_got, msg='The lsf job id was not parsed correctly')

    def test_gets_lsf_job_resources_params_correctly_when_no_script(self):
        """
        Tests that if can get the parameters string for the bsub command correctly when there is no script defined
        """
        with self.flask_app.app_context():
            job_type = 'TEST'
            docker_image_url = 'some_url'

            input_files_desc, input_files_hashes, params = self.prepare_mock_job_args()
            job = delayed_job_models.get_or_create(job_type, params, docker_image_url, input_files_hashes)

            resources_params_got = job_submission_service.get_job_resources_params(job)
            resources_params_must_be = ''

            self.assertEqual(resources_params_got, resources_params_must_be,
                             msg='The resources params were not calculated correctly!')

    def test_gets_lsf_job_resources_params_correctly_when_script_returns_default(self):
        """
        Tests that if can get the parameters string for the bsub command correctly when script returns default
        """
        with self.flask_app.app_context():
            job_type = 'TEST'
            docker_image_url = 'some_url'

            input_files_desc, input_files_hashes, params = self.prepare_mock_job_args()
            job = delayed_job_models.get_or_create(job_type, params, docker_image_url, input_files_hashes)
            job_submission_service.create_job_run_dir(job)

            test_job_config = delayed_job_models.get_job_config(job_type)

            source_requirements_script_path = 'requirements.py'
            with open(source_requirements_script_path, 'wt') as requirements_script:
                requirements_script.write('#!/usr/bin/env python3\n')
                requirements_script.write('print("DEFAULT")\n')

            test_job_config.requirements_script_path = source_requirements_script_path


            resources_params_got = job_submission_service.get_job_resources_params(job)
            resources_params_must_be = ''

            self.assertEqual(resources_params_got, resources_params_must_be,
                             msg='The resources params were not calculated correctly!')


            job_requirements_script_path = Path(job.run_dir_path).joinpath('requirements_calculation.py')

            self.assertTrue(os.path.isfile(job_requirements_script_path),
                            msg='The requirements script was not created!')

            os.remove(source_requirements_script_path)

    def test_gets_lsf_job_resources_params_correctly_when_script_returns_some_params(self):
        """
        Tests that if can get the parameters string for the bsub command correctly when script returns default
        """
        with self.flask_app.app_context():
            job_type = 'TEST'
            docker_image_url = 'some_url'

            input_files_desc, input_files_hashes, params = self.prepare_mock_job_args()
            job = delayed_job_models.get_or_create(job_type, params, docker_image_url, input_files_hashes)
            job_submission_service.create_job_run_dir(job)

            test_job_config = delayed_job_models.get_job_config(job_type)

            print('job.run_dir_path: ', job.run_dir_path)
            resources_params_must_be = '-n 2 -M 8192 -R "rusage[mem=8192]"'
            source_requirements_script_path = 'requirements.py'
            with open(source_requirements_script_path, 'wt') as requirements_script:
                requirements_script.write('#!/usr/bin/env python3\n')
                requirements_script.write(f'print(\'{resources_params_must_be}\')\n')

            test_job_config.requirements_script_path = source_requirements_script_path


            resources_params_got = job_submission_service.get_job_resources_params(job)


            self.assertEqual(resources_params_got, resources_params_must_be,
                             msg='The resources params were not calculated correctly!')

            job_requirements_script_path = Path(job.run_dir_path).joinpath('requirements_calculation.py')
            print('job_requirements_script_path: ', job_requirements_script_path)

            self.assertTrue(os.path.isfile(job_requirements_script_path),
                            msg='The requirements script was not created!')

            os.remove(source_requirements_script_path)

