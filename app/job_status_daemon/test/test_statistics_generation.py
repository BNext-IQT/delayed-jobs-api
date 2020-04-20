"""
This Module tests the statistics generation of the status daemon
"""
import unittest
import shutil

from app import create_app
from app.models import delayed_job_models
from app.job_status_daemon import daemon

class TestJobStatisticsGeneration(unittest.TestCase):
    """
    Class to test the generation of statistics by the status daemon
    """
    def setUp(self):
        self.flask_app = create_app()
        self.client = self.flask_app.test_client()

        with self.flask_app.app_context():
            delayed_job_models.delete_all_jobs()
            shutil.rmtree(daemon.AGENT_RUN_DIR, ignore_errors=True)

    def tearDown(self):
        with self.flask_app.app_context():
            delayed_job_models.delete_all_jobs()
            shutil.rmtree(daemon.AGENT_RUN_DIR, ignore_errors=True)

    # def simulate_finished_job(self):
    #     """
    #     Creates a job that finished normally in the database
    #     """
    #
    #     job = delayed_job_models.DelayedJob(
    #         id=f'Job-{assigned_host}-{status}',
    #         type='TEST',
    #         lsf_job_id=i,
    #         status=status,
    #         lsf_host=assigned_host,
    #         run_environment=run_environment
    #     )

    def test_generates_statistics_for_a_finished_job(self):
        """
        tests that generates the statistics for a job that finished normally
        """
        print('TEST STATS FOR A FINISHED JOB')
