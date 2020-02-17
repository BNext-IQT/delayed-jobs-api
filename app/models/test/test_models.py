"""
Tests for the delayed job model
"""
import base64
import datetime
import hashlib
import json
import unittest
from pathlib import Path

from app import create_app
from app.models import delayed_job_models


class TestModels(unittest.TestCase):
    """
    Class to test CRUD operation in the delayed job models
    """
    OUT_RUN_DIR_NAME = 'test_out_dir'
    ABS_OUT_DIR_PATH = str(Path(OUT_RUN_DIR_NAME).resolve())

    def setUp(self):
        self.flask_app = create_app()
        self.client = self.flask_app.test_client()

    def tearDown(self):

        with self.flask_app.app_context():
            delayed_job_models.delete_all_jobs()

    def test_job_id_is_generated_correctly(self):
        """
        Tests that a job id is generated correctly from hashing its parameters.
        """
        job_type = 'SIMILARITY'

        params = {
            'search_type': 'SIMILARITY',
            'structure': '[H]C1(CCCN1C(=N)N)CC1=NC(=NO1)C1C=CC(=CC=1)NC1=NC(=CS1)C1C=CC(Br)=CC=1',
            'threshold': '70'
        }

        # A structure with the hashes of the input files influences the job id
        input_files_hashes = {
            'input1': 'hash1-hash1-hash1-hash1-hash1-hash1-hash1',
            'input2': 'hash2-hash2-hash2-hash2-hash2-hash2-hash2',
        }

        docker_image_url = 'some_url'

        id_got = delayed_job_models.generate_job_id(job_type, params, docker_image_url, input_files_hashes)

        all_params = {
            **params,
            'job_input_files_hashes':{
                **input_files_hashes
            },
            'docker_image_url': docker_image_url
        }

        print('ALL PARAMS: ', all_params)

        stable_raw_search_params = json.dumps(all_params, sort_keys=True)
        search_params_digest = hashlib.sha256(stable_raw_search_params.encode('utf-8')).digest()
        base64_search_params_digest = base64.b64encode(search_params_digest).decode('utf-8').replace('/', '_').replace(
            '+', '-')

        id_must_be = '{}-{}'.format(repr(job_type), base64_search_params_digest)
        self.assertEqual(id_must_be, id_got, msg='The job id was not generated correctly!')

    def test_a_job_is_created(self):
        """
        Tests that a job is created correctly
        """

        with self.flask_app.app_context():
            job_type = 'SIMILARITY'
            params = {
                'search_type': 'SIMILARITY',
                'structure': '[H]C1(CCCN1C(=N)N)CC1=NC(=NO1)C1C=CC(=CC=1)NC1=NC(=CS1)C1C=CC(Br)=CC=1',
                'threshold': '70'
            }
            docker_image_url_must_be = 'some_url'

            job_must_be = delayed_job_models.get_or_create(job_type, params, docker_image_url_must_be)
            job_id_must_be = job_must_be.id
            job_got = delayed_job_models.DelayedJob.query.filter_by(id=job_id_must_be).first()
            self.assertEqual(job_type, job_got.type, msg='The job type was not saved correctly.')
            self.assertEqual(delayed_job_models.JobStatuses.CREATED, job_got.status,
                             msg='The job status was not saved correctly.')
            self.assertEqual(0, job_got.progress, msg='The job progress was not saved correctly.')

            created_at_got = job_got.created_at.timestamp()
            created_at_must_be = datetime.datetime.utcnow().timestamp()
            self.assertAlmostEqual(created_at_got, created_at_must_be, places=1,
                                   msg='The created time was not calculated correctly')

            params_must_be = json.dumps(params)
            params_got = job_got.raw_params
            self.assertEqual(params_got, params_must_be, msg='The parameters where not saved correctly')

            docker_image_url_got = job_got.docker_image_url
            self.assertEqual(docker_image_url_got, docker_image_url_must_be,
                             msg='The docker image url was not saved correctly')

    def test_a_job_is_created_only_once(self):
        """
        Tests that there can only exist one job instance with given a set of parameters.
        """

        with self.flask_app.app_context():
            job_type = 'SIMILARITY'
            params = {
                'search_type': 'SIMILARITY',
                'structure': '[H]C1(CCCN1C(=N)N)CC1=NC(=NO1)C1C=CC(=CC=1)NC1=NC(=CS1)C1C=CC(Br)=CC=1',
                'threshold': '70'
            }
            docker_image_url = 'some_url'

            # Create a job and set status as finished
            job_0 = delayed_job_models.get_or_create(job_type, params, docker_image_url)
            status_must_be = delayed_job_models.JobStatuses.FINISHED
            job_0.status = status_must_be

            # Create a job with exactly the same params
            job_1 = delayed_job_models.get_or_create(job_type, params, docker_image_url)

            # they must be the same
            self.assertEqual(job_0.id, job_1.id, msg='A job with the same params was created twice!')
            self.assertEqual(job_1.status, status_must_be, msg='A job with the same params was created twice!')


if __name__ == '__main__':
    unittest.main()
