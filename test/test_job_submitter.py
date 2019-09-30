"""
This module tests jobs submission to the EBI queue
"""
import unittest
import getpass


class TestJobSubmitter(unittest.TestCase):
    """
    Class to test job submission
    """

    # pylint: disable=no-self-use
    def test_job_can_be_submitted(self):
        """
        Test that a job can be submitted
        """
        username = getpass.getuser()
        print('HERE I TEST THAT I CAN SUBMIT A JOB')
        print('My username is: ', username)
