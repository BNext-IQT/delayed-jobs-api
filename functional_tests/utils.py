"""
Module with utils functions for the functional tests
"""
import os

import requests
from requests.auth import HTTPBasicAuth


def prepare_test_job_1(tmp_dir):
    """
    create some inputs, some parameters for a test job
    :return: a dict with the test job properties
    """

    os.makedirs(tmp_dir, exist_ok=True)
    files = {}
    for i in range(0, 2):
        file_name = f'input_{i}.txt'
        test_file_i_path = tmp_dir.joinpath(file_name)
        with open(test_file_i_path, 'wt') as test_file:
            test_file.write(f'this is input file {i}')

        files[file_name] = open(test_file_i_path, 'rb')

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
    files = {}
    for i in range(0, 2):
        file_name = f'input_{i}.txt'
        test_file_i_path = tmp_dir.joinpath(file_name)
        with open(test_file_i_path, 'wt') as test_file:
            test_file.write(f'Input file {i}')

        files[file_name] = open(test_file_i_path, 'rb')

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
                               f'(Status code: {login_request.status_code}')

    login_response = login_request.json()
    print('Token obtained')
    admin_token = login_response.get('token')
    headers = {'X-Admin-Key': admin_token}

    jobs_deletion_url = f'{server_base_url}/admin/delete_all_jobs_by_type'
    jobs_deletion_request = requests.post(jobs_deletion_url, data={'job_type': 'TEST'}, headers=headers)
    if jobs_deletion_request.status_code != 200:
        raise ServerAdminError(f'There was a problem when requesting the deletion of test jobs! '
                               f'(Status code: {jobs_deletion_request.status_code}')
    jobs_deletion_response = jobs_deletion_request.json()

    print('jobs_deletion_response: ', jobs_deletion_response)
