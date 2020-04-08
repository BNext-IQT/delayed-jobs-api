"""
Tests that a failing job is restarted up to n times when it is submitted again
"""
import time
import datetime
from pathlib import Path
import shutil

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

    job_id = submit_job_and_confirm(server_base_url, test_job_to_submit)

    print('Waiting until job fails')

    started_at_0, job_status = get_job_started_at_and_status(server_base_url, job_id)
    assert job_status == 'ERROR', 'Job should have failed!'

    max_retries = 7 # The server only allows to retry a job 6 times
    retries = 0
    previous_started_at_time = started_at_0
    original_job_id = job_id
    while retries < max_retries:

        print(f'Now I will submit the same job again. Retry number {retries + 1}')
        if retries == (max_retries - 1):
            print('This time the job should not run again')

        test_job_to_submit = utils.prepare_test_job_3(tmp_dir)

        job_id = submit_job_and_confirm(server_base_url, test_job_to_submit)

        assert original_job_id == job_id, 'The job id must be the same!'

        print('Waiting until job fails')

        started_at_1 = assert_job_must_have_not_been_started_with_retries(server_base_url, job_id, retries, max_retries,
                                                       previous_started_at_time)

        previous_started_at_time = started_at_1

        retries += 1

    shutil.rmtree(tmp_dir)

def submit_job_and_confirm(server_base_url, test_job_to_submit):

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

    return job_id

def get_job_started_at_and_status(server_base_url, job_id):

    status_url = utils.get_status_url(server_base_url, job_id)
    print('status_url: ', status_url)

    utils.assert_job_status_with_retries(status_url, 'ERROR')

    status_request = requests.get(status_url)
    status_response = status_request.json()

    started_at = datetime.datetime.strptime(status_response.get('started_at'), '%Y-%m-%d %H:%M:%S')
    print(f'started_at: {started_at}')

    job_status = status_response.get('status')
    print(f'job_status: {job_status}')

    return started_at, job_status

def get_job_started_at_and_assert_status_with_retries(server_base_url, job_id):

    status_url = utils.get_status_url(server_base_url, job_id)
    utils.assert_job_status_with_retries(status_url, 'ERROR')

    started_at_1, job_status = get_job_started_at_and_status(server_base_url, job_id)
    assert job_status == 'ERROR', 'Job should have failed!'

    return started_at_1

def assert_job_must_have_not_been_started_with_retries(server_base_url, job_id, job_retries, max_job_retries,
                                                       previous_started_at_time):
    max_test_retries = 1000
    current_test_tries = 0
    assertion_passed = False

    while current_test_tries < max_test_retries:

        started_at_1 = get_job_started_at_and_assert_status_with_retries(server_base_url, job_id)

        print(f'job_retries: {job_retries}')
        print(f'max_job_retries: {max_job_retries}')
        print(f'previous_started_at_time: {previous_started_at_time}')
        print(f'started_at_1: {started_at_1}')

        if job_retries < (max_job_retries - 1):
            assertion_passed = previous_started_at_time != started_at_1
        else:
            assertion_passed = previous_started_at_time == started_at_1

        if assertion_passed:
            break

        current_test_tries += 1

    if job_retries < (max_job_retries - 1):
        assert assertion_passed, 'The job must have started again'
    else:
        assert assertion_passed, 'The job must have NOT started again, ' \
                                                         'max retries have been reached'

    return started_at_1