#!/usr/bin/env python3
import argparse
import yaml
import json
from common import job_utils
import requests


parser = argparse.ArgumentParser()
parser.add_argument('run_params_file', help='The path of the file with the run params')
parser.add_argument('-v', '--verbose', help='Make output verbose', action="store_true")
parser.add_argument('-n', '--dry-run', help='Make output verbose', action='store_true', dest='dry_run')
args = parser.parse_args()

RUN_PARAMS = {}
WEB_SERVICES_BASE_URL = 'https://www.ebi.ac.uk/chembl/api/data'
LIMIT_PER_PAGE = 1000

# TODO: define error class, use it when there is an error from web services to report it.


def run():

    global RUN_PARAMS
    RUN_PARAMS = yaml.load(open(args.run_params_file, 'r'), Loader=yaml.FullLoader)
    job_params = json.loads(RUN_PARAMS.get('job_params'))

    server_base_url = RUN_PARAMS.get('status_update_endpoint').get('url')
    job_token = RUN_PARAMS.get('job_token')

    server_connection = job_utils.ServerConnection(server_base_url=server_base_url,
                                                   job_token=job_token,
                                                   verbose=args.verbose,
                                                   dry_run=args.dry_run)

    server_connection.update_job_status(job_utils.Statuses.RUNNING)
    server_connection.log('Execution Started')

    print_if_verbose('job_params: ', json.dumps(job_params, indent=4))

    api_initial_url = ''
    search_type = job_params.get('search_type')
    if search_type == 'SIMILARITY':
        search_term = job_params.get('structure')
        threshold = job_params.get('threshold')
        api_initial_url = f'{WEB_SERVICES_BASE_URL}/similarity/{search_term}/{threshold}.json' \
                          f'?limit={LIMIT_PER_PAGE}&only=molecule_chembl_id,similarity'

    print_if_verbose('api_initial_url: ', api_initial_url)

    server_connection.update_api_initial_url(api_initial_url)

    results = []
    search_url = api_initial_url
    more_results_to_load = True
    while more_results_to_load:

        server_connection.log(f'Loading page: {search_url}')

        r = requests.get(search_url)
        response = r.json()
        print('response: ', response)
        append_to_results_from_response_page(response, results, search_type)

        more_results_to_load = False


def print_if_verbose(*args):

    if args.verbose:
        print(args)


def append_to_results_from_response_page(response, results, search_type):

    print('append_to_results_from_response_page')
    error_message = response.get('error_message', 'Error with sim search!')
    print('error_message: ', error_message)

    if error_message is not None:
        raise search_manager.SSSearchError(error_message)

    return

    if search_type == SSSearchJob.SIMILARITY:

        for r in response['molecules']:
            results.append({
                'molecule_chembl_id': r['molecule_chembl_id'],
                'similarity': float(r['similarity'])
            })

    elif search_type == SSSearchJob.SUBSTRUCTURE or search_type == SSSearchJob.CONNECTIVITY:

        for r in response['molecules']:
            results.append(r)


if __name__ == "__main__":
    run()