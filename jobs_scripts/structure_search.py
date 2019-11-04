#!/usr/bin/env python3
import argparse
import yaml
import json
from common import job_utils


parser = argparse.ArgumentParser()
parser.add_argument('run_params_file', help='The path of the file with the run params')
parser.add_argument('-v', '--verbose', help='Make output verbose', action="store_true")
args = parser.parse_args()

RUN_PARAMS = {}
WEB_SERVICES_BASE_URL = 'https://www.ebi.ac.uk/chembl/api/data'
LIMIT_PER_PAGE = 1000


def run():

    global RUN_PARAMS
    RUN_PARAMS = yaml.load(open(args.run_params_file, 'r'), Loader=yaml.FullLoader)
    job_params = json.loads(RUN_PARAMS.get('job_params'))

    server_base_url = RUN_PARAMS.get('status_update_endpoint').get('url')
    job_token = RUN_PARAMS.get('job_token')

    server_connection = job_utils.ServerConnection(server_base_url=server_base_url,
                                                   job_token=job_token,
                                                   verbose=args.verbose)

    server_connection.update_job_status(job_utils.Statuses.RUNNING)
    server_connection.log('Execution Started')

    if args.verbose:
        print('job_params: ', json.dumps(job_params, indent=4))

    api_initial_url = ''
    search_type = job_params.get('search_type')
    if search_type == 'SIMILARITY':
        search_term = job_params.get('structure')
        threshold = job_params.get('threshold')
        api_initial_url = f'{WEB_SERVICES_BASE_URL}/similarity/{search_term}/{threshold}.json?limit={LIMIT_PER_PAGE}'

    if args.verbose:
        print('api_initial_url: ', api_initial_url)

    server_connection.update_api_initial_url(api_initial_url)


if __name__ == "__main__":
    run()