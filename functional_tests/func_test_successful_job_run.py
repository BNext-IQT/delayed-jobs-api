"""
Module that runs a normal simple job and expects it to run correctly.
"""
import time
from pathlib import Path
import shutil

import requests

import utils


def run_test(server_base_url, admin_username, admin_password):
    """
    Tests that a job can run normally.
    :param server_base_url: base url of the running server. E.g. http://127.0.0.1:5000
    """

    print('------------------------------------------------------------------------------------------------')
    print('Going to test a successful job run')
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

    print('wait some time until it starts, it should be running...')

    status_url = utils.get_status_url(server_base_url, job_id)
    print('status_url: ', status_url)

    utils.assert_job_status_with_retries(status_url, 'RUNNING', 'FINISHED')

    print('waiting time until it finishes...')

    utils.assert_job_status_with_retries(status_url, 'FINISHED')
    status_request = requests.get(status_url)
    status_response = status_request.json()
    job_progress = int(status_response.get('progress'))
    assert job_progress == 100, 'The final progress of the job must be 100!'

    utils.assert_output_files_can_be_downloaded(status_response)

    utils.request_all_test_jobs_deletion(server_base_url, admin_username, admin_password)
    shutil.rmtree(tmp_dir)
