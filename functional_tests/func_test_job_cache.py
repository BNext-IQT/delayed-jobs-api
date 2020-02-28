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
    shutil.rmtree(tmp_dir)

    submit_url = utils.get_submit_url(server_base_url)
    print('submit_url: ', submit_url)

    submit_request = requests.post(submit_url, data=test_job_to_submit['payload'], files=test_job_to_submit['files'])
    submission_status_code = submit_request.status_code
    print(f'submission_status_code: {submission_status_code}')
    assert submission_status_code == 200, 'Job could not be submitted!'
    submit_response = submit_request.json()
    job_id = submit_response.get('job_id')

    print('Waiting until job finishes')
    time.sleep(10)

    status_url = utils.get_status_url(server_base_url, job_id)
    print('status_url: ', status_url)

    status_request = requests.get(status_url)
    status_response = status_request.json()

    started_at_0 = datetime.datetime.strptime(status_response.get('started_at'), '%Y-%m-%d %H:%M:%S.%f')
    timestamp_0 = started_at_0.timestamp()
    print(f'timestamp_0: {timestamp_0}')
    print(f'started_at_0: {started_at_0}')

    print('Now I will submit the same job again')
    submit_request = requests.post(submit_url, data=test_job_to_submit['payload'], files=test_job_to_submit['files'])
    submit_response = submit_request.json()
    job_id = submit_response.get('id')

    print('Waiting until job finishes')
    time.sleep(1)

    status_request = requests.get(f'{server_base_url}/status/{job_id}')
    status_response = status_request.json()
    started_at_1 = datetime.datetime.strptime(status_response.get('started_at'), '%Y-%m-%d %H:%M:%S.%f')
    timestamp_1 = started_at_1.timestamp()
    print(f'timestamp_1: {timestamp_1}')
    print(f'started_at_1: {started_at_1}')

    assert started_at_0 == started_at_1, 'The job must have not started again'

    output_files_urls = status_response.get('output_files_urls')
    print('output_files_urls: ', output_files_urls)

    for url in output_files_urls:
        file_request = requests.get(url)
        assert file_request.status_code == 200, 'A results file could not be downloaded!!'

