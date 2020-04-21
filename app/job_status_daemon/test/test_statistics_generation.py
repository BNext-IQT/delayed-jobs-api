"""
This Module tests the statistics generation of the status daemon
"""
import unittest
import shutil
from datetime import datetime, timedelta

from app import create_app
from app.models import delayed_job_models
from app.job_status_daemon import daemon
from app.job_status_daemon.job_statistics import statistics_generator

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

    def test_calculates_time_from_created_to_running(self):
        """
        test that it calculates the time from created to running
        """

        current_time = datetime.now()
        created_at = current_time
        seconds_must_be = 1.5
        started_at = created_at + timedelta(seconds=seconds_must_be)

        job = delayed_job_models.DelayedJob(
            id=f'Job-Finished',
            type='TEST',
            created_at=created_at,
            started_at=started_at
        )

        seconds_got = statistics_generator.get_seconds_from_created_to_queued(job)
        self.assertEqual(seconds_got, seconds_must_be,
                         msg='The seconds from created to queued were not calculated correctly!')

    def test_calculates_time_from_running_to_finished(self):
        """
        test that it calculates the time from running to finished
        """

        current_time = datetime.now()
        started_at = current_time
        seconds_must_be = 1.5
        finished_at = started_at + timedelta(seconds=seconds_must_be)

        job = delayed_job_models.DelayedJob(
            id=f'Job-Finished',
            type='TEST',
            started_at=started_at,
            finished_at=finished_at
        )

        seconds_got = statistics_generator.get_seconds_from_running_to_finished(job)
        self.assertEqual(seconds_got, seconds_must_be,
                         msg='The seconds from created to queued were not calculated correctly!')



