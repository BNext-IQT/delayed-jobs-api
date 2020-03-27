"""
    Module that runs tests for job caching
"""
import time
import datetime
import shutil
from pathlib import Path

import requests

import utils


# pylint: disable=R0914
def run_test(server_base_url, admin_username, admin_password):
    """
    Test that when a job that is submitted is has exactly the same parameters of a previously run job, the job is not
    run again. It just returns the existing job.
    :param server_base_url: base url of the running server. E.g. http://127.0.0.1:5000
    """

    print('------------------------------------------------------------------------------------------------')
    print('Going to test the job caching')
    print('------------------------------------------------------------------------------------------------')

    utils.request_all_test_jobs_deletion(server_base_url, admin_username, admin_password)

    tmp_dir = Path().absolute().joinpath('tmp')
    test_job_to_submit = utils.prepare_test_job_2(tmp_dir)

    submit_url = utils.get_submit_url(server_base_url)
    print('submit_url: ', submit_url)

    submit_request = requests.post(submit_url, data=test_job_to_submit['payload'], files=test_job_to_submit['files'])
    submission_status_code = submit_request.status_code
    print(f'submission_status_code: {submission_status_code}')
    assert submission_status_code == 200, 'Job could not be submitted!'
    submit_response = submit_request.json()
    print('submit_response: ', submit_response)
    job_id = submit_response.get('job_id')

    print('Waiting until job finishes')

    status_url = utils.get_status_url(server_base_url, job_id)
    utils.assert_job_status_with_retries(status_url, 'FINISHED')

    status_request = requests.get(status_url)
    status_response = status_request.json()
    print('status_response: ', status_response)

    started_at_0 = datetime.datetime.strptime(status_response.get('started_at'), '%Y-%m-%d %H:%M:%S')
    timestamp_0 = started_at_0.timestamp()
    print(f'timestamp_0: {timestamp_0}')
    print(f'started_at_0: {started_at_0}')

    print('Now I will submit the same job again')
    test_job_to_submit = utils.prepare_test_job_2(tmp_dir)
    submit_request = requests.post(submit_url, data=test_job_to_submit['payload'], files=test_job_to_submit['files'])
    submit_response = submit_request.json()
    job_id_1 = submit_response.get('job_id')

    assert job_id == job_id_1, 'The job ids must be the same!'

    print('Waiting until job "starts"')
    utils.assert_job_status_with_retries(status_url, 'RUNNING')

    status_url = utils.get_status_url(server_base_url, job_id_1)
    print('status_url: ', status_url)
    status_request = requests.get(status_url)
    status_response = status_request.json()

    print('status_response: ', status_response)
    started_at_1 = datetime.datetime.strptime(status_response.get('started_at'), '%Y-%m-%d %H:%M:%S')
    timestamp_1 = started_at_1.timestamp()
    print(f'timestamp_1: {timestamp_1}')
    print(f'started_at_1: {started_at_1}')

    assert started_at_0 == started_at_1, f'The job must have not started again. ' \
                                         f'started_at_0:{started_at_0}, started_at_1:{started_at_1}'

    utils.assert_output_files_can_be_downloaded(status_response)

    shutil.rmtree(tmp_dir)

