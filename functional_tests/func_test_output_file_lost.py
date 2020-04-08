"""
    Module that runs tests when an output file of a job goes missing
"""
import time
import datetime
from pathlib import Path
import shutil

import requests

import utils


def run_test(server_base_url, admin_username, admin_password):
    """
    Tests that when an output file of a job is missing, the job is started again.
    :param server_base_url: base url of the running server. E.g. http://127.0.0.1:5000
    """

    print('------------------------------------------------------------------------------------------------')
    print('Going to test the loss of a results file')
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

    submission_response = submit_request.json()
    print('submission_response: ', submission_response)
    job_id = submission_response.get('job_id')

    print('wait some time until it finishes')

    status_url = utils.get_status_url(server_base_url, job_id)
    utils.assert_job_status_with_retries(status_url, 'FINISHED')

    status_request = requests.get(status_url)
    status_response = status_request.json()
    print('status_response: ', status_response)
    started_at_0 = datetime.datetime.strptime(status_response.get('started_at'), '%Y-%m-%d %H:%M:%S')
    print(f'started_at_0: {started_at_0}')

    print('Now I am going to simulate the loss of the outputs')

    utils.request_all_job_outputs_deletion(job_id, server_base_url, admin_username, admin_password)

    print('Now I will submit the same job again')

    test_job_to_submit = utils.prepare_test_job_2(tmp_dir)
    print('submit_url: ', submit_url)
    submit_request = requests.post(submit_url, data=test_job_to_submit['payload'], files=test_job_to_submit['files'])
    submit_response = submit_request.json()
    job_id = submit_response.get('job_id')

    print('Wait a bit again until it finishes')
    utils.assert_job_status_with_retries(status_url, 'FINISHED')

    status_url = utils.get_status_url(server_base_url, job_id)
    print('status_url: ', status_url)

    status_request = requests.get(status_url)

    status_response = status_request.json()
    print('status_response: ', status_response)
    started_at_1 = datetime.datetime.strptime(status_response.get('started_at'), '%Y-%m-%d %H:%M:%S')
    print(f'started_at_1: {started_at_1}')

    assert started_at_0 != started_at_1, 'The job must have started again'

    shutil.rmtree(tmp_dir)
