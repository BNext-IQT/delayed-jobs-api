"""
This module tests jobs submission to the EBI queue
"""
import unittest

from app import create_app
from app.apis.models import delayed_job_models
from app.db import db
from app.job_submitter import job_submitter

flask_app = create_app()
db.init_app(flask_app)


class TestJobSubmitter(unittest.TestCase):
    """
    Class to test job submission
    """

    def setUp(self):
        with flask_app.app_context():
            db.create_all()

    # pylint: disable=no-self-use
    def test_job_can_be_submitted(self):
        """
        Test that a job can be submitted
        """
        with flask_app.app_context():
            job_type = delayed_job_models.JobTypes.SIMILARITY
            params = {
                'structure': '[H]C1(CCCN1C(=N)N)CC1=NC(=NO1)C1C=CC(=CC=1)NC1=NC(=CS1)C1C=CC(Br)=CC=1',
                'threshold': '70'
            }
            job_submitter.submit_job(job_type, params)