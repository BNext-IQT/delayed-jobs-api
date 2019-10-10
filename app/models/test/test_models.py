"""
Tests for the delayed job model
"""
import unittest
import app.models.delayed_job as DelayedJob
import json
import hashlib
import base64


class MyTestCase(unittest.TestCase):

    def test_job_id_is_generated_correctly(self):
        job_type = DelayedJob.JobTypes.SIMILARITY
        params = {
            'structure': '[H]C1(CCCN1C(=N)N)CC1=NC(=NO1)C1C=CC(=CC=1)NC1=NC(=CS1)C1C=CC(Br)=CC=1',
            'threshold': '70'
        }
        id_got = DelayedJob.generate_job_id(job_type, params)

        stable_raw_search_params = json.dumps(params, sort_keys=True)
        search_params_digest = hashlib.sha256(stable_raw_search_params.encode('utf-8')).digest()
        base64_search_params_digest = base64.b64encode(search_params_digest).decode('utf-8').replace('/', '_').replace(
            '+', '-')

        id_must_be = '{}-{}'.format(repr(job_type), base64_search_params_digest)
        self.assertEqual(id_must_be, id_got, msg='The job id was not generated correctly!')

    def test_a_job_is_created(self):
        job_type = DelayedJob.JobTypes.SIMILARITY
        params = {
            'structure': '[H]C1(CCCN1C(=N)N)CC1=NC(=NO1)C1C=CC(=CC=1)NC1=NC(=CS1)C1C=CC(Br)=CC=1',
            'threshold': '70'
        }

        job_must_be = DelayedJob.get_or_create(job_type, params)
        job_id_must_be = job_must_be.id
        print('job_id_must_be: ', job_id_must_be)


if __name__ == '__main__':
    unittest.main()
