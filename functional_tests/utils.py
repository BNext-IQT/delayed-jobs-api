"""
Module with utils functions for the functional tests
"""
import os
import time
import datetime

import requests
from requests.auth import HTTPBasicAuth

def create_mock_input_files_for_job(tmp_dir, filename_prefix):

    files = {}
    for i in range(0, 2):
        file_name = f'{filename_prefix}_input_{i}.txt'
        test_file_i_path = tmp_dir.joinpath(file_name)

        if os.path.isfile(test_file_i_path):
            os.remove(test_file_i_path)

        with open(test_file_i_path, 'wt') as test_file:
            test_file.write(f'this is input file {i}')

        files[file_name] = open(test_file_i_path, 'rb')

    return files

def prepare_test_job_1(tmp_dir):
    """
    create some inputs, some parameters for a test job
    :return: a dict with the test job properties
    """
    os.makedirs(tmp_dir, exist_ok=True)
    files = create_mock_input_files_for_job(tmp_dir, 'job1')

    seconds = 20
    payload = {
        'instruction': 'RUN_NORMALLY',
        'seconds': seconds,
        'api_url': 'https://www.ebi.ac.uk/chembl/api/data/similarity/CN1C(=O)C=C(c2cccc(Cl)c2)c3cc(ccc13)[C@@](N)(c4ccc(Cl)cc4)c5cncn5C/80.json',
        'dl__ignore_cache': True
    }

    print('payload: ', payload)
    print('files: ', files)

    return {
        'payload': payload,
        'files': files
    }

def prepare_test_job_2(tmp_dir):
    """
    create some inputs, some parameters for a test job
    :return: a dict with the test job properties
    """
    os.makedirs(tmp_dir, exist_ok=True)
    files = create_mock_input_files_for_job(tmp_dir, 'job2')

    seconds = 5
    payload = {
        'instruction': 'RUN_NORMALLY',
        'seconds': seconds,
        'api_url': 'https://www.ebi.ac.uk/chembl/api/data/similarity/CN1C(=O)C=C(c2cccc(Cl)c2)c3cc(ccc13)[C@@](N)(c4ccc(Cl)cc4)c5cncn5C/80.json',
        'dl__ignore_cache': False
    }

    print('payload: ', payload)
    print('files: ', files)

    return {
        'payload': payload,
        'files': files
    }

def prepare_test_job_3(tmp_dir):
    """
    create some inputs, some parameters for a test job
    :return: a dict with the test job properties
    """
    os.makedirs(tmp_dir, exist_ok=True)
    files = create_mock_input_files_for_job(tmp_dir, 'job2')

    seconds = 1
    payload = {
        'instruction': 'FAIL',
        'seconds': seconds,
        'api_url': 'https://www.ebi.ac.uk/chembl/api/data/similarity/CN1C(=O)C=C(c2cccc(Cl)c2)c3cc(ccc13)[C@@](N)(c4ccc(Cl)cc4)c5cncn5C/80.json',
        'dl__ignore_cache': False
    }

    print('payload: ', payload)
    print('files: ', files)

    return {
        'payload': payload,
        'files': files
    }

def get_submit_url(server_base_url):
    """
    :param server_base_url: the base url of the server
    :return: the url used to submit jobs
    """
    return f'{server_base_url}/submit/test_job'

def get_status_url(server_base_url, job_id):
    """
    Returns the status url to check a job given its ID
    :param server_base_url: the base url of the server
    :param job_id: job id to check
    """
    return f'{server_base_url}/status/{job_id}'

# ----------------------------------------------------------------------------------------------------------------------
# Server Administration Helpers
# ----------------------------------------------------------------------------------------------------------------------
class ServerAdminError(Exception):
    """Base class for exceptions in the admin functions."""


def request_all_test_jobs_deletion(server_base_url, admin_username, admin_password):
    """
    Requests the server to delete all test jobs. Useful to run before the start of a test.
    """

    admin_login_url = f'{server_base_url}/admin/login'
    print('admin_login_url: ', admin_login_url)
    login_request = requests.get(admin_login_url, auth=HTTPBasicAuth(admin_username, admin_password))

    if login_request.status_code != 200:
        raise ServerAdminError(f'There was a problem when logging into the administration of the system! '
                               f'(Status code: {login_request.status_code})')

    login_response = login_request.json()
    print('Token obtained')

    admin_token = login_response.get('token')
    headers = {'X-Admin-Key': admin_token}

    jobs_deletion_url = f'{server_base_url}/admin/delete_all_jobs_by_type'
    jobs_deletion_request = requests.post(jobs_deletion_url, data={'job_type': 'TEST'}, headers=headers)
    if jobs_deletion_request.status_code != 200:
        raise ServerAdminError(f'There was a problem when requesting the deletion of test jobs! '
                               f'(Status code: {jobs_deletion_request.status_code})')
    jobs_deletion_response = jobs_deletion_request.json()

    print('jobs_deletion_response: ', jobs_deletion_response)

def request_all_job_outputs_deletion(job_id, server_base_url, admin_username, admin_password):
    """
    Requests the deletion of the outputs of a job
    :param job_id: the id of the job for which delete the outputs
    :param server_base_url: base url of the server
    :param admin_username: admin username
    :param admin_password: admin password
    """
    admin_login_url = f'{server_base_url}/admin/login'
    print('admin_login_url: ', admin_login_url)
    login_request = requests.get(admin_login_url, auth=HTTPBasicAuth(admin_username, admin_password))

    if login_request.status_code != 200:
        raise ServerAdminError(f'There was a problem when logging into the administration of the system! '
                               f'(Status code: {login_request.status_code})')

    login_response = login_request.json()
    print('Token obtained')

    admin_token = login_response.get('token')
    headers = {'X-Admin-Key': admin_token}

    jobs_output_deletion_url = f'{server_base_url}/admin/delete_output_files_for_job/{job_id}'
    job_output_deletion_request = requests.get(jobs_output_deletion_url, headers=headers)
    if job_output_deletion_request.status_code != 200:
        raise ServerAdminError(f'There was a problem when requesting the deletion of the output of the job: {job_id}'
                               f'(Status code: {job_output_deletion_request.status_code})')
    jobs_deletion_response = job_output_deletion_request.json()

    print('jobs_deletion_response: ', jobs_deletion_response)

def assert_job_status_with_retries(status_url, status_must_be_1, status_must_be_2=None):
    """
    Asserts that the status is what it should be. It retries up to 5 times
    :param status_url: url to check status
    :param status_must_be_1: what the status should be
    :param status_must_be_2: another option for that the status must be
    """
    time.sleep(10)
    max_retries = 1000
    current_tries = 0
    assertion_passed = False

    while current_tries < max_retries:

        status_request = requests.get(status_url)
        status_response = status_request.json()

        job_status = status_response.get('status')
        job_progress = status_response.get('progress')
        print(f'{datetime.datetime.utcnow().isoformat()} - job_status: {job_status} progress: {job_progress}')
        assertion_passed = job_status == status_must_be_1 or job_status == status_must_be_2
        current_tries += 1

        if assertion_passed:
            break

        time.sleep(1)

    assert assertion_passed, f'Job seems to not be {status_must_be_1}! after {current_tries} tries.'

def assert_output_files_can_be_downloaded(status_response):
    """
    asserts that the output files can be downloaded
    :param status_response: status response from the server
    """
    time.sleep(5)
    output_files_urls = status_response.get('output_files_urls')
    print('output_files_urls: ', output_files_urls)

    for output_key, url in output_files_urls.items():
        full_url = f'http://{url}'
        file_request = requests.get(full_url)
        assert file_request.status_code == 200, f'A results file ({full_url}) could not be downloaded!!'



