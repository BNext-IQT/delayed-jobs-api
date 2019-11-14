#!/usr/bin/env python3
import argparse
import yaml
import json
from common import job_utils
import requests
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('run_params_file', help='The path of the file with the run params')
parser.add_argument('-v', '--verbose', help='Make output verbose', action="store_true")
parser.add_argument('-n', '--dry-run', help='Make output verbose', action='store_true', dest='dry_run')
args = parser.parse_args()

RUN_PARAMS = {}
EBI_BASE_URL = 'https://www.ebi.ac.uk'
WEB_SERVICES_BASE_URL = f'{EBI_BASE_URL}/chembl/api/data'
LIMIT_PER_PAGE = 5


class SearchError(Exception):
    """Base class for exceptions in this module."""
    pass


SIMILARITY = 'SIMILARITY'
SUBSTRUCTURE = 'SUBSTRUCTURE'
CONNECTIVITY = 'CONNECTIVITY'


def run():
    global RUN_PARAMS
    RUN_PARAMS = yaml.load(open(args.run_params_file, 'r'), Loader=yaml.FullLoader)
    job_params = json.loads(RUN_PARAMS.get('job_params'))

    server_connection = job_utils.ServerConnection(run_params_file=args.run_params_file, verbose=args.verbose)

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
    else:
        api_initial_url = f'{WEB_SERVICES_BASE_URL}/substructure/{search_term}.json' \
                          f'?limit={LIMIT_PER_PAGE}&only=molecule_chembl_id'

    print_if_verbose('api_initial_url: ', api_initial_url)
    server_connection.update_api_initial_url(api_initial_url)

    results = []
    search_url = api_initial_url
    num_loaded_items = 0
    more_results_to_load = True
    while more_results_to_load:

        server_connection.log(f'Loading page: {search_url}')

        r = requests.get(search_url)
        status_code = r.status_code
        response = r.json()

        server_connection.log(f'status_code: {status_code}')
        if status_code != 200:
            server_connection.update_job_status(job_utils.Statuses.ERROR)
            return
        try:
            num_loaded_items += append_to_results_from_response_page(response, results, search_type)
        except SearchError as e:
            server_connection.log(f'Error: {repr(e)}')
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
    if args.verbose:
        print(print_args)


def append_to_results_from_response_page(response, results, search_type):

    error_message = response.get('error_message')

    if error_message is not None:
        raise SearchError(error_message)

    if search_type == SIMILARITY:

        for r in response['molecules']:
            results.append({
                'molecule_chembl_id': r['molecule_chembl_id'],
                'similarity': float(r['similarity'])
            })

    elif search_type == SUBSTRUCTURE or search_type == CONNECTIVITY:

        for r in response['molecules']:
            results.append(r)

    return len(response['molecules'])


if __name__ == "__main__":
    run()
