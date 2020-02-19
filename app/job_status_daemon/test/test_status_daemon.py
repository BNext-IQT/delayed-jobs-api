"""
This Module tests the basic functions of the status daemon
"""
import unittest
import socket
from pathlib import Path
from datetime import datetime
from os import path
import shutil
import os

from sqlalchemy import and_

from app import create_app
from app.models import delayed_job_models
from app.config import RUN_CONFIG
from app.job_status_daemon import daemon


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
            shutil.rmtree(daemon.AGENT_RUN_DIR, ignore_errors=True)

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
                        status=status,
                        lsf_host=assigned_host
                    )
                    delayed_job_models.save_job(job)
                    i += 1

    def create_test_jobs_1(self):
        """
        This will create:
        - 2 Jobs in error state, each running in a different lsf cluster
        - 2 Jobs in finished state, each running in a different lsf cluster
        """
        with self.flask_app.app_context():

            i = 0
            for status in [delayed_job_models.JobStatuses.FINISHED,
                           delayed_job_models.JobStatuses.ERROR]:

                lsf_config = RUN_CONFIG.get('lsf_submission')
                lsf_host = lsf_config['lsf_host']

                for assigned_host in [lsf_host, 'another_host']:
                    job = delayed_job_models.DelayedJob(
                        id=f'Job-{assigned_host}-{status}',
                        type='TEST',
                        lsf_job_id=i,
                        status=status,
                        lsf_host=assigned_host
                    )
                    delayed_job_models.save_job(job)
                    i += 1

    def test_determines_for_which_jobs_check_status_0(self):
        """
        Given a set of jobs currently in the database, knows for which it is required to check the status.
        In this case, some jobs require a check.
        """
        self.create_test_jobs_0()

        with self.flask_app.app_context():
            lsf_config = RUN_CONFIG.get('lsf_submission')
            lsf_host = lsf_config['lsf_host']

            status_is_not_error_or_finished = delayed_job_models.DelayedJob.status.notin_(
                [delayed_job_models.JobStatuses.ERROR, delayed_job_models.JobStatuses.FINISHED]
            )
            lsf_host_is_my_host = delayed_job_models.DelayedJob.lsf_host == lsf_host

            job_to_check_status_must_be = delayed_job_models.DelayedJob.query.filter(
                and_(lsf_host_is_my_host, status_is_not_error_or_finished)
            )

            lsf_ids_to_check_status_must_be = [job.lsf_job_id for job in job_to_check_status_must_be]
            lsf_ids_to_check_got = daemon.get_lsf_job_ids_to_check()
            self.assertListEqual(lsf_ids_to_check_status_must_be, lsf_ids_to_check_got,
                                 msg='The jobs for which to check the status were not created correctly!')


    def test_determines_for_which_jobs_check_status_1(self):
        """
        Given a set of jobs currently in the database, knows for which it is required to check the status.
        In this case, NO jobs require a check.
        """
        self.create_test_jobs_1()

        with self.flask_app.app_context():
            lsf_ids_to_check_status_must_be = []
            lsf_ids_to_check_got = daemon.get_lsf_job_ids_to_check()
            self.assertListEqual(lsf_ids_to_check_status_must_be, lsf_ids_to_check_got,
                                 msg='The jobs for which to check the status were not created correctly!')


    def test_produces_a_correct_job_status_check_script_path(self):
        """
        Test that produces a correct path for the job status script
        """

        filename = f'{datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}_check_lsf_job_status.sh'
        job_status_check_script_path_must_be = Path(daemon.AGENT_RUN_DIR).joinpath(socket.gethostname(), filename)

        job_status_check_script_path_got = daemon.get_check_job_status_script_path()

        # remove the last character (the second) to avoid annoying false negatives
        self.assertEqual(str(job_status_check_script_path_must_be)[:-1], str(job_status_check_script_path_got)[:-1],
                         msg='The path for the job status checking job was not produced correctly!')


    def test_prepares_the_job_status_script(self):
        """
        Test that the job status script is created and can be executed.
        """
        self.create_test_jobs_0()

        with self.flask_app.app_context():

            lsf_ids_to_check = daemon.get_lsf_job_ids_to_check()
            script_path_got = daemon.prepare_job_status_check_script(lsf_ids_to_check)
            self.assertTrue(path.isfile(script_path_got), msg='The job status check script has not been created!')

            self.assertTrue(os.access(script_path_got, os.X_OK),
                            msg=f'The script file for the job ({script_path_got}) is not executable!')

    def load_sample_file(self, file_path):
        """
        Loads a file with a sample read from the path specified as a parameter
        :param file_path: path of the sample
        :return: a string with the contents of the file
        """
        sample_output_file_path = Path(file_path).resolve()
        with open(sample_output_file_path, 'rt') as sample_output_file:
            sample_output = sample_output_file.read()
            return sample_output

    def test_parses_the_output_of_bjobs_when_no_jobs_were_found(self):
        """
        Generates mock jobs, then sends a mock output to the the function to test that it interpreted the output
        accordingly
        """
        self.create_test_jobs_0()
        sample_output = self.load_sample_file('app/job_status_daemon/test/data/sample_lsf_output_0.txt')

        with self.flask_app.app_context():
            daemon.parse_bjobs_output(sample_output)
            # No status should have changed

            for status_must_be in [delayed_job_models.JobStatuses.CREATED, delayed_job_models.JobStatuses.QUEUED,
                           delayed_job_models.JobStatuses.RUNNING, delayed_job_models.JobStatuses.FINISHED,
                           delayed_job_models.JobStatuses.ERROR]:

                lsf_config = RUN_CONFIG.get('lsf_submission')
                lsf_host = lsf_config['lsf_host']

                for assigned_host in [lsf_host, 'another_host']:

                    id_to_check = f'Job-{assigned_host}-{status_must_be}'
                    job = delayed_job_models.get_job_by_id(id_to_check)
                    status_got = job.status
                    self.assertEqual(status_got, status_must_be,
                                     msg='The status was modified! This should have not modified the status')


    def test_parses_the_output_of_bjobs_running_job(self):
        """
        Generates mock jobs, then sends a mock output to the the function to test that it interpreted the output
        accordingly. This test focuses on a job that switched to running state.
        """
        self.create_test_jobs_0()

        sample_output = self.load_sample_file('app/job_status_daemon/test/data/sample_lsf_output_1.txt')

        with self.flask_app.app_context():
            daemon.parse_bjobs_output(sample_output)
            # job with lsf id 0 should be in running state now
            lsf_job_id = 0
            job = delayed_job_models.get_job_by_lsf_id(lsf_job_id)
            status_got = job.status
            status_must_be = delayed_job_models.JobStatuses.RUNNING
            self.assertEqual(status_got, status_must_be, msg='The status of the job was not changed accordingly!')

    def test_parses_the_output_of_bjobs_pending_job(self):
        """
        Generates mock jobs, then sends a mock output to the the function to test that it interpreted the output
        accordingly. This test focuses on a job that switched to pending state.
        """
        self.create_test_jobs_0()

        sample_output = self.load_sample_file('app/job_status_daemon/test/data/sample_lsf_output_2.txt')

        with self.flask_app.app_context():
            daemon.parse_bjobs_output(sample_output)
            # job with lsf id 0 should be in running state now
            lsf_job_id = 0
            job = delayed_job_models.get_job_by_lsf_id(lsf_job_id)
            status_got = job.status
            status_must_be = delayed_job_models.JobStatuses.QUEUED
            self.assertEqual(status_got, status_must_be, msg='The status of the job was not changed accordingly!')

    def test_parses_the_output_of_bjobs_error_job(self):
        """
        Generates mock jobs, then sends a mock output to the the function to test that it interpreted the output
        accordingly. This test focuses on a job that switched to error state.
        """
        self.create_test_jobs_0()

        sample_output = self.load_sample_file('app/job_status_daemon/test/data/sample_lsf_output_1.txt')

        with self.flask_app.app_context():
            daemon.parse_bjobs_output(sample_output)
            # job with lsf id 0 should be in running state now
            lsf_job_id = 2
            job = delayed_job_models.get_job_by_lsf_id(lsf_job_id)
            status_got = job.status
            status_must_be = delayed_job_models.JobStatuses.ERROR
            self.assertEqual(status_got, status_must_be, msg='The status of the job was not changed accordingly!')


    def test_parses_the_output_of_bjobs_finished_job(self):
        """
        Generates mock jobs, then sends a mock output to the the function to test that it interpreted the output
        accordingly. This test focuses on a job that switched to finished state.
        """
        self.create_test_jobs_0()

        sample_output = self.load_sample_file('app/job_status_daemon/test/data/sample_lsf_output_1.txt')

        with self.flask_app.app_context():
            daemon.parse_bjobs_output(sample_output)
            # job with lsf id 0 should be in running state now
            lsf_job_id = 4
            job = delayed_job_models.get_job_by_lsf_id(lsf_job_id)
            status_got = job.status
            status_must_be = delayed_job_models.JobStatuses.FINISHED
            self.assertEqual(status_got, status_must_be, msg='The status of the job was not changed accordingly!')
