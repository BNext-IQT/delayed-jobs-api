"""
This Module tests the basic functions of the status daemon
"""
import unittest

from app import create_app

class TestJobStatusDaemon(unittest.TestCase):
    """
    Class to test Job Status Daemon
    """

    def setUp(self):
        self.flask_app = create_app()
        self.client = self.flask_app.test_client()

    def tearDown(self):
        print('TEAR DOWN')

    def test_determines_for_which_jobs_check_status_0(self):
        """
        Given a set of jobs currently in the database, knows for which it is required to check the status.
        In this case, some jobs require a check.
        """
        print('TEST FOR WHICH JOB CHECK JOB STATUS')


    def test_mapping_of_lsf_job_status(self):

        print('TEST MAPPING OF JOB STATUS')