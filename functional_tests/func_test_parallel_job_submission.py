"""
    Module that runs tests for parallel job submission
"""
import time
import datetime
from pathlib import Path
import shutil

import requests

import utils


def run_test(server_base_url, admin_username, admin_password):
    """
    Submits a job, and while it is running it submits another job with exactly the same parameters. No new job should be
    started, it should return the id for the job that is already running without restarting it.
    :param server_base_url: base url of the running server. E.g. http://127.0.0.1:5000
    """

    print('------------------------------------------------------------------------------------------------')
    print('Going to test the when a job is submitted while the same job is already running')
    print('------------------------------------------------------------------------------------------------')

    utils.request_all_test_jobs_deletion(server_base_url, admin_username, admin_password)

    tmp_dir = Path().absolute().joinpath('tmp')
    test_job_to_submit = utils.prepare_test_job_1(tmp_dir)

    submit_url = utils.get_submit_url(server_base_url)
    print('submit_url: ', submit_url)
    submit_request = requests.post(submit_url, data=test_job_to_submit['payload'], files=test_job_to_submit['files'])
    submission_status_code = submit_request.status_code
    print(f'submission_status_code: {submission_status_code}')
    assert submission_status_code == 200, 'Job could not be submitted!'

    submission_response = submit_request.json()
    print('submission_response: ', submission_response)
    job_id = submission_response.get('job_id')

    print('Waiting until should be running')
    time.sleep(10)

    status_url = utils.get_status_url(server_base_url, job_id)
    print('status_url: ', status_url)

    status_request = requests.get(status_url)
    status_response = status_request.json()
    started_at_0 = datetime.datetime.strptime(status_response.get('started_at'), '%Y-%m-%d %H:%M:%S')
    timestamp_0 = started_at_0.timestamp()
    print(f'timestamp_0: {timestamp_0}')
    print(f'started_at_0: {started_at_0}')

    print('Now I will submit the same job again')
    test_job_to_submit = utils.prepare_test_job_1(tmp_dir)
    print('submit_url: ', submit_url)
    submit_request = requests.post(submit_url, data=test_job_to_submit['payload'], files=test_job_to_submit['files'])
    submit_response = submit_request.json()
    job_id = submit_response.get('job_id')

    print('Wait a bit again')
    time.sleep(1)

    status_url = utils.get_status_url(server_base_url, job_id)
    print('status_url: ', status_url)

    status_request = requests.get(status_url)

    status_response = status_request.json()
    started_at_1 = datetime.datetime.strptime(status_response.get('started_at'), '%Y-%m-%d %H:%M:%S')
    timestamp_1 = started_at_1.timestamp()
    print(f'timestamp_1: {timestamp_1}')
    print(f'started_at_1: {started_at_1}')

    assert started_at_0 == started_at_1, 'The job must have not started again'

    shutil.rmtree(tmp_dir)
