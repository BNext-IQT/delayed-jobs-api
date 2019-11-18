"""
Tests that a failing job is restarted up to n times when it is submitted again
"""
import time
import datetime

import requests


# pylint: disable=R0914
# pylint: disable=R0915
def run_test(server_base_url):
    """
    Submits a job that will always fail and tests that it is restarted when submitted again. But only up to n times
    :param server_base_url: base url of the running server. E.g. http://127.0.0.1:5000
    """

    print('------------------------------------------------------------------------------------------------')
    print('Going to test the a job that always fails')
    print('------------------------------------------------------------------------------------------------')

    submit_url = f'{server_base_url}/submit/test_job/'
    print('submit_url: ', submit_url)
    seconds = 1
    payload = {
        'instruction': 'FAIL',
        'seconds': seconds
    }

    print('payload: ', payload)

    submit_request = requests.post(submit_url, json=payload)
    submit_response = submit_request.json()
    job_id = submit_response.get('id')

    print('Waiting until job finishes')
    time.sleep(seconds + 1)

    status_request = requests.get(f'{server_base_url}/status/{job_id}')
    status_response = status_request.json()
    started_at_0 = datetime.datetime.strptime(status_response.get('started_at'), '%Y-%m-%d %H:%M:%S.%f')
    timestamp_0 = started_at_0.timestamp()
    print(f'timestamp_0: {timestamp_0}')
    print(f'started_at_0: {started_at_0}')

    job_status = status_response.get('status')
    print(f'job_status: {job_status}')
    assert job_status == 'ERROR', 'Job should have failed!'

    max_retries = 6
    retries = 0
    while retries < max_retries:

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
        print(f'started_at_0: {started_at_0}')
        print(f'timestamp_1: {timestamp_1}')
        print(f'started_at_1: {started_at_1}')

        assert started_at_0 != started_at_1, 'The job must have started again'

        job_status = status_response.get('status')
        started_at_0 = datetime.datetime.strptime(status_response.get('started_at'), '%Y-%m-%d %H:%M:%S.%f')
        print(f'job_status: {job_status}')
        retries += 1

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
