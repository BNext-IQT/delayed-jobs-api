#!/usr/bin/env python3
"""
    Script that runs requests the deletion of expired jobs
"""
import argparse
import requests
from requests.auth import HTTPBasicAuth


PARSER = argparse.ArgumentParser()
PARSER.add_argument('server_base_path', help='server base path to run the tests against',
                    default='http://127.0.0.1:5000', nargs='?')
PARSER.add_argument('admin_username', help='Admin username',
                    default='admin', nargs='?')
PARSER.add_argument('admin_password', help='Admin password',
                    default='123456', nargs='?')
ARGS = PARSER.parse_args()

class ServerAdminError(Exception):
    """Base class for exceptions in the admin functions."""

def run():
    """
    Runs the script
    """
    print(f'Requesting deletion of expired jobs on {ARGS.server_base_path}')

    server_base_url = ARGS.server_base_path
    admin_username = ARGS.admin_username
    admin_password = ARGS.admin_password

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

    jobs_deletion_url = f'{server_base_url}/admin/delete_expired_jobs'

    jobs_deletion_request = requests.get(jobs_deletion_url, headers=headers)
    if jobs_deletion_request.status_code != 200:
        raise ServerAdminError(f'There was a problem when requesting the deletion of test jobs! '
                               f'(Status code: {jobs_deletion_request.status_code})')
    jobs_deletion_response = jobs_deletion_request.json()

    print('jobs_deletion_response: ', jobs_deletion_response)

if __name__ == "__main__":
    run()