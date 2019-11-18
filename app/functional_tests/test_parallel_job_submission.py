"""
    Module that runs tests for parallel job submission
"""
import time
import datetime

import requests


def run_test(server_base_url):
    """
    Submits a job, and while it is running it submits another job with exactly the same parameters. No new job should be
    started, it should return the id for the job that is already running without restarting it.
    :param server_base_url: base url of the running server. E.g. http://127.0.0.1:5000
    """

    print('------------------------------------------------------------------------------------------------')
    print('Going to test the when a job is submitted while the same job is already running')
    print('------------------------------------------------------------------------------------------------')

    submit_url = f'{server_base_url}/submit/test_job/'
    print('submit_url: ', submit_url)
    seconds = 3
    payload = {
        'instruction': 'RUN_NORMALLY',
        'seconds': seconds
    }

    print('payload: ', payload)

    submit_request = requests.post(submit_url, json=payload)
    submit_response = submit_request.json()
    job_id = submit_response.get('id')

    print('Waiting until should be running')
    time.sleep(seconds / 2)

    status_request = requests.get(f'{server_base_url}/status/{job_id}')
    status_response = status_request.json()
    started_at_0 = datetime.datetime.strptime(status_response.get('started_at'), '%Y-%m-%d %H:%M:%S.%f')
    timestamp_0 = started_at_0.timestamp()
    print(f'timestamp_0: {timestamp_0}')
    print(f'started_at_0: {started_at_0}')

    print('Now I will submit the same job again')
    submit_request = requests.post(submit_url, json=payload)
    submit_response = submit_request.json()
    job_id = submit_response.get('id')

    print('Wait a bit again')
    time.sleep(seconds / 2)

    status_request = requests.get(f'{server_base_url}/status/{job_id}')
    status_response = status_request.json()
    started_at_1 = datetime.datetime.strptime(status_response.get('started_at'), '%Y-%m-%d %H:%M:%S.%f')
    timestamp_1 = started_at_1.timestamp()
    print(f'timestamp_1: {timestamp_1}')
    print(f'started_at_1: {started_at_1}')

    assert started_at_0 == started_at_1, 'The job must have not started again'
