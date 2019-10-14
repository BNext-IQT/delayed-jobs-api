"""
Tests for the delayed job model
"""
import unittest
from app.models import delayed_job_models
import json
import hashlib
import base64
from app.models.db import db
from app import create_app
import datetime

flask_app = create_app()
db.init_app(flask_app)


class MyTestCase(unittest.TestCase):

    def setUp(self):
        with flask_app.app_context():
            db.create_all()

    def test_job_id_is_generated_correctly(self):
        job_type = delayed_job_models.JobTypes.SIMILARITY
        params = {
            'structure': '[H]C1(CCCN1C(=N)N)CC1=NC(=NO1)C1C=CC(=CC=1)NC1=NC(=CS1)C1C=CC(Br)=CC=1',
            'threshold': '70'
        }
        id_got = delayed_job_models.generate_job_id(job_type, params)

        stable_raw_search_params = json.dumps(params, sort_keys=True)
        search_params_digest = hashlib.sha256(stable_raw_search_params.encode('utf-8')).digest()
        base64_search_params_digest = base64.b64encode(search_params_digest).decode('utf-8').replace('/', '_').replace(
            '+', '-')

        id_must_be = '{}-{}'.format(repr(job_type), base64_search_params_digest)
        self.assertEqual(id_must_be, id_got, msg='The job id was not generated correctly!')

    def test_a_job_is_created(self):

        with flask_app.app_context():
            job_type = delayed_job_models.JobTypes.SIMILARITY
            params = {
                'structure': '[H]C1(CCCN1C(=N)N)CC1=NC(=NO1)C1C=CC(=CC=1)NC1=NC(=CS1)C1C=CC(Br)=CC=1',
                'threshold': '70'
            }

            job_must_be = delayed_job_models.get_or_create(job_type, params)
            job_id_must_be = job_must_be.id
            print('job_id_must_be: ', job_id_must_be)
            job_got = delayed_job_models.DelayedJob.query.filter_by(id=job_id_must_be).first()
            self.assertEqual(job_type, job_got.type, msg='The job type was not saved correctly.')
            self.assertEqual(delayed_job_models.JobStatuses.CREATED, job_got.status,
                             msg='The job status was not saved correctly.')
            self.assertEqual(0, job_got.progress, msg='The job progress was not saved correctly.')

            created_at_got = job_got.created_at.timestamp()
            created_at_must_be = datetime.datetime.utcnow().timestamp()
            self.assertAlmostEqual(created_at_got, created_at_must_be, places=1,
                                   msg='The created time was not calculated correctly')


if __name__ == '__main__':
    unittest.main()
