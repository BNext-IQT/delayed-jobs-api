"""
Module that runs a normal simple job and expects it to run correctly.
"""
import time
from pathlib import Path
import os
import shutil

import requests

import utils


def run_test(server_base_url):
    """
    Tests that a job can run normally.
    :param server_base_url: base url of the running server. E.g. http://127.0.0.1:5000
    """

    print('------------------------------------------------------------------------------------------------')
    print('Going to test a successful job run')
    print('------------------------------------------------------------------------------------------------')

    tmp_dir = Path().absolute().joinpath('tmp')
    test_job_to_submit = utils.prepare_test_job_1(tmp_dir)

    shutil.rmtree(tmp_dir)

    submit_url = utils.get_submit_url(server_base_url)
    print('submit_url: ', submit_url)
    submit_request = requests.post(submit_url, data=test_job_to_submit['payload'], files=test_job_to_submit['files'])
    submission_status_code = submit_request.status_code
    print(f'submission_status_code: {submission_status_code}')
    assert submission_status_code == 200, 'Job could not be submitted!'

    submission_response = submit_request.json()
    print('submission_response: ', submission_response)
    job_id = submission_response.get('job_id')

    print('wait some time until it starts, it should be running...')
    time.sleep(10)

    status_url = f'{server_base_url}/status/{job_id}'
    print('status_url: ', status_url)

    status_request = requests.get(status_url)
    status_response = status_request.json()

    job_status = status_response.get('status')
    print(f'job_status: {job_status}')
    assert job_status == 'RUNNING', 'Job seems to not be running!'

    progress = int(status_response.get('progress'))
    print(f'progress:  {progress}')
    assert progress > 0, 'The job progress is not increasing'

    print('wait some time until it should have finished...')
    time.sleep(seconds + 10)

    status_request = requests.get(status_url)
    status_response = status_request.json()

    job_status = status_response.get('status')
    print(f'job_status: {job_status}')
    assert job_status == 'FINISHED', 'Job should have finished already!'

    output_files_urls = status_response.get('output_files_urls')
    print('output_files_urls: ', output_files_urls)

    for url in output_files_urls:
        file_request = requests.get(url)
        assert file_request.status_code == 200, 'A results file could not be downloaded!!'
