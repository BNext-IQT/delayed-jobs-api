"""
This Module tests the basic functions of the status daemon
"""
import unittest

from app import create_app
from app.models import delayed_job_models
from app.config import RUN_CONFIG


class TestJobStatusDaemon(unittest.TestCase):
    """
    Class to test Job Status Daemon
    """

    def setUp(self):
        self.flask_app = create_app()
        self.client = self.flask_app.test_client()

    def tearDown(self):
        with self.flask_app.app_context():
            delayed_job_models.delete_all_jobs()

    def create_test_jobs_0(self):
        """
        This will create:
        - 2 Jobs in created state, each running in a different lsf cluster
        - 2 Jobs in queued state, each running in a different lsf cluster
        - 2 Jobs in running state, each running in a different lsf cluster
        - 2 Jobs in error state, each running in a different lsf cluster
        - 2 Jobs in finished state, each running in a different lsf cluster
        """
        with self.flask_app.app_context():

            i = 0
            for status in [delayed_job_models.JobStatuses.CREATED, delayed_job_models.JobStatuses.QUEUED,
                           delayed_job_models.JobStatuses.RUNNING, delayed_job_models.JobStatuses.FINISHED,
                           delayed_job_models.JobStatuses.ERROR]:

                lsf_config = RUN_CONFIG.get('lsf_submission')
                lsf_host = lsf_config['lsf_host']

                for assigned_host in [lsf_host, 'another_host']:

                    job = delayed_job_models.DelayedJob(
                        id=f'Job-{assigned_host}-{status}',
                        type='TEST',
                        lsf_job_id=i,
                        status=delayed_job_models.JobStatuses.CREATED,
                        lsf_host=assigned_host
                    )
                    delayed_job_models.save_job(job)
                    i += 1


    def test_determines_for_which_jobs_check_status_0(self):
        """
        Given a set of jobs currently in the database, knows for which it is required to check the status.
        In this case, some jobs require a check.
        """
        print('TEST FOR WHICH JOB CHECK JOB STATUS')
        self.create_test_jobs_0()


    def test_mapping_of_lsf_job_status(self):

        print('TEST MAPPING OF JOB STATUS')