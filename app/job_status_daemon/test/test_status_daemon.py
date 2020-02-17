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

    def test_mapping_of_lsf_job_status(self):

        print('TEST MAPPING OF JOB STATUS')