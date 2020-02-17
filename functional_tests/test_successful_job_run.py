"""
Module that runs a normal simple job and expects it to run correctly.
"""
import time

import requests


def run_test(server_base_url):
    """
    Tests that a job can run normally.
    :param server_base_url: base url of the running server. E.g. http://127.0.0.1:5000
    """

    print('------------------------------------------------------------------------------------------------')
    print('Going to test a successful job run')
    print('------------------------------------------------------------------------------------------------')

    submit_url = f'{server_base_url}/submit/test_job/'
    print('submit_url: ', submit_url)
    seconds = 6
    payload = {
        'instruction': 'RUN_NORMALLY',
        'seconds': seconds
    }

    print('payload: ', payload)

    submit_request = requests.post(submit_url, json=payload)
    assert submit_request.status_code == 200, 'Job could not be submitted!'

    submit_response = submit_request.json()
    job_id = submit_response.get('id')

    print('wait some time until it starts, it should be running...')
    time.sleep(seconds/2)

    status_request = requests.get(f'{server_base_url}/status/{job_id}')
    status_response = status_request.json()

    job_status = status_response.get('status')
    print(f'job_status: {job_status}')
    assert job_status == 'RUNNING', 'Job seems to not be running!'

    progress = int(status_response.get('progress'))
    print(f'progress:  {progress}')
    assert progress > 0, 'The job progress is not increasing'

    print('wait some time until it should have finished...')
    time.sleep((seconds / 2) + 1)

    status_request = requests.get(f'{server_base_url}/status/{job_id}')
    status_response = status_request.json()

    job_status = status_response.get('status')
    print(f'job_status: {job_status}')
    assert job_status == 'FINISHED', 'Job should have finished already!'

    output_file_url = status_response.get('output_file_url')
    full_output_file_url = f'{server_base_url}{output_file_url}'
    print(f'full_output_file_url: {full_output_file_url}')
    file_request = requests.get(full_output_file_url)
    assert file_request.status_code == 200, 'The results file could not be downloaded!!'
