#!/usr/bin/env python3
"""
Script that runs structure searches using the ChEMBL web services
"""
import argparse
import json
from pathlib import Path
import requests

import yaml

from common import job_utils

# pylint: disable=too-many-locals
PARSER = argparse.ArgumentParser()
PARSER.add_argument('run_params_file', help='The path of the file with the run params')
PARSER.add_argument('-v', '--verbose', help='Make output verbose', action="store_true")
PARSER.add_argument('-n', '--dry-run', help='Make output verbose', action='store_true', dest='dry_run')
ARGS = PARSER.parse_args()


EBI_BASE_URL = 'https://www.ebi.ac.uk'
WEB_SERVICES_BASE_URL = f'{EBI_BASE_URL}/chembl/api/data'
LIMIT_PER_PAGE = 5


class SearchError(Exception):
    """Base class for exceptions in this module."""


SIMILARITY = 'SIMILARITY'
SUBSTRUCTURE = 'SUBSTRUCTURE'
CONNECTIVITY = 'CONNECTIVITY'


def run():
    """
    Runs the job
    """

    run_params = yaml.load(open(ARGS.run_params_file, 'r'), Loader=yaml.FullLoader)
    job_params = json.loads(run_params.get('job_params'))

    server_connection = job_utils.ServerConnection(run_params_file=ARGS.run_params_file, verbose=ARGS.verbose)
    server_connection.update_job_status(job_utils.Statuses.RUNNING)
    server_connection.log('Execution Started')

    print_if_verbose('job_params: ', json.dumps(job_params, indent=4))

    api_initial_url = ''
    search_type = job_params.get('search_type')
    search_term = job_params.get('structure')

    if search_type == SIMILARITY:
        threshold = job_params.get('threshold')
        api_initial_url = f'{WEB_SERVICES_BASE_URL}/similarity/{search_term}/{threshold}.json' \
                          f'?limit={LIMIT_PER_PAGE}&only=molecule_chembl_id,similarity'
    elif search_type == SUBSTRUCTURE:
        api_initial_url = f'{WEB_SERVICES_BASE_URL}/substructure/{search_term}.json' \
                          f'?limit={LIMIT_PER_PAGE}&only=molecule_chembl_id'
    elif search_type == CONNECTIVITY:
        api_initial_url = f'{WEB_SERVICES_BASE_URL}/molecule.json?limit={LIMIT_PER_PAGE}' \
                          f'&only=molecule_chembl_id&molecule_structures__canonical_smiles__flexmatch={search_term}'

    print_if_verbose('api_initial_url: ', api_initial_url)
    server_connection.update_api_initial_url(api_initial_url)

    results = []
    search_url = api_initial_url
    num_loaded_items = 0
    more_results_to_load = True
    while more_results_to_load:

        server_connection.log(f'Loading page: {search_url}')

        request = requests.get(search_url)
        status_code = request.status_code
        response = request.json()

        server_connection.log(f'status_code: {status_code}')
        if status_code != 200:
            server_connection.update_job_status(job_utils.Statuses.ERROR)
            return
        try:
            num_loaded_items += append_to_results_from_response_page(response, results, search_type)
        except SearchError as error:
            error_msg = repr(error)
            server_connection.log(f'Error: {error_msg}')
            server_connection.update_job_status(job_utils.Statuses.ERROR, error_msg)
            return

        meta = response.get('page_meta')

        total_count = meta.get('total_count')
        progress_percentage = int((num_loaded_items / total_count) * 100)
        server_connection.update_job_progress(progress_percentage)

        next_url = meta.get('next')
        more_results_to_load = next_url is not None
        if more_results_to_load:
            search_url = f'{EBI_BASE_URL}{next_url}'

    results_file_name = 'results.json'
    with open(results_file_name, 'w') as out_file:
        out_file.write(json.dumps(results))

    server_connection.upload_job_results_file(str(Path(results_file_name).resolve()))
    server_connection.update_job_status(job_utils.Statuses.FINISHED)
    server_connection.log('Job finished correctly!')


def print_if_verbose(*print_args):
    """
    Calls the print function if verbose setting is True
    :param args: arguments for print
    """
    if ARGS.verbose:
        print(*print_args)


def append_to_results_from_response_page(response, results, search_type):
    """
    Appends to the results list new results from the response obtainer
    :param response: response dict from server
    :param results: results list that accumulates the results
    :param search_type: SIMILARITY, SUBSTRUCTURE, CONNECTIVITY
    """

    error_message = response.get('error_message')

    if error_message is not None:
        raise SearchError(error_message)

    if search_type == SIMILARITY:

        for result in response['molecules']:
            results.append({
                'molecule_chembl_id': result['molecule_chembl_id'],
                'similarity': float(result['similarity'])
            })

    elif search_type in [SUBSTRUCTURE, CONNECTIVITY]:

        for result in response['molecules']:
            results.append(result)

    return len(response['molecules'])


if __name__ == "__main__":
    run()
