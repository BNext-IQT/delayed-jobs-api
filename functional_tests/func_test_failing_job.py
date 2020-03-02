"""
Tests that a failing job is restarted up to n times when it is submitted again
"""
import time
import datetime
from pathlib import Path

import requests

import utils


# pylint: disable=R0914
# pylint: disable=R0915
def run_test(server_base_url, admin_username, admin_password):
    """
    Submits a job that will always fail and tests that it is restarted when submitted again. But only up to n times
    :param server_base_url: base url of the running server. E.g. http://127.0.0.1:5000
    """

    print('------------------------------------------------------------------------------------------------')
    print('Going to test the a job that always fails')
    print('------------------------------------------------------------------------------------------------')

    utils.request_all_test_jobs_deletion(server_base_url, admin_username, admin_password)
    tmp_dir = Path().absolute().joinpath('tmp')
    test_job_to_submit = utils.prepare_test_job_3(tmp_dir)

    submit_url = utils.get_submit_url(server_base_url)
    print('submit_url: ', submit_url)
    submit_request = requests.post(submit_url, data=test_job_to_submit['payload'], files=test_job_to_submit['files'])
    submission_status_code = submit_request.status_code
    print(f'submission_status_code: {submission_status_code}')
    assert submission_status_code == 200, 'Job could not be submitted!'

    submission_response = submit_request.json()
    print('submission_response: ', submission_response)
    job_id = submission_response.get('job_id')

    print('Waiting until job finishes')
    time.sleep(20)

    status_url = utils.get_status_url(server_base_url, job_id)
    print('status_url: ', status_url)

    status_request = requests.get(status_url)
    status_response = status_request.json()
    started_at_0 = datetime.datetime.strptime(status_response.get('started_at'), '%Y-%m-%d %H:%M:%S')
    timestamp_0 = started_at_0.timestamp()
    print(f'timestamp_0: {timestamp_0}')
    print(f'started_at_0: {started_at_0}')

    job_status = status_response.get('status')
    print(f'job_status: {job_status}')
    assert job_status == 'ERROR', 'Job should have failed!'

    max_retries = 6
    retries = 0
    previous_started_at_time = started_at_0
    original_job_id = job_id
    while retries < max_retries:

        print(f'Now I will submit the same job again. Retry number {retries + 1}')
        test_job_to_submit = utils.prepare_test_job_3(tmp_dir)

        submit_url = utils.get_submit_url(server_base_url)
        print('submit_url: ', submit_url)
        submit_request = requests.post(submit_url, data=test_job_to_submit['payload'],
                                       files=test_job_to_submit['files'])
        submission_status_code = submit_request.status_code
        print(f'submission_status_code: {submission_status_code}')
        assert submission_status_code == 200, 'Job could not be submitted!'

        submission_response = submit_request.json()
        print('submission_response: ', submission_response)
        job_id = submission_response.get('job_id')

        assert original_job_id == job_id, 'The job id must be the same!'

        print('Waiting until job finishes')
        time.sleep(20)

        status_url = utils.get_status_url(server_base_url, job_id)
        print('status_url: ', status_url)

        status_request = requests.get(status_url)

        status_response = status_request.json()
        print('status_response: ', status_response)

        started_at_1 = datetime.datetime.strptime(status_response.get('started_at'), '%Y-%m-%d %H:%M:%S')
        timestamp_1 = started_at_1.timestamp()
        job_status = status_response.get('status')
        print(f'job_status: {job_status}')
        assert job_status == 'ERROR', 'Job should have failed!'

        print(f'previous_started_at_time: {previous_started_at_time}')
        print(f'timestamp_1: {timestamp_1}')
        print(f'started_at_1: {started_at_1}')

        assert previous_started_at_time != started_at_1, 'The job must have started again'
        previous_started_at_time = started_at_1

        job_status = status_response.get('status')
        print(f'job_status: {job_status}')
        assert job_status == 'ERROR', 'Job should have failed!'

        retries += 1

    return

    print(f'Now I will submit the same job again. Retry number {retries}')
    submit_request = requests.post(submit_url, json=payload)
    submit_response = submit_request.json()
    job_id = submit_response.get('id')

    print('Waiting until job finishes')
    time.sleep(seconds + 1)

    status_request = requests.get(f'{server_base_url}/status/{job_id}')
    status_response = status_request.json()
    started_at_1 = datetime.datetime.strptime(status_response.get('started_at'), '%Y-%m-%d %H:%M:%S.%f')
    timestamp_1 = started_at_1.timestamp()
    print(f'timestamp_1: {timestamp_1}')
    print(f'started_at_1: {started_at_1}')

    assert started_at_0 == started_at_1, 'The job must have not started again, the max retries limit was reached.'
