#!/usr/bin/env python3
"""
Script that collects data from elasctisearch and generates a file with it.
"""
import json
import argparse

import yaml
import requests

from common import job_utils

PARSER = argparse.ArgumentParser()
PARSER.add_argument('run_params_file', help='The path of the file with the run params')
PARSER.add_argument('-v', '--verbose', help='Make output verbose', action='store_true')
ARGS = PARSER.parse_args()

COLUMNS_CONFIG_URL_TEMPLATE = 'https://www.ebi.ac.uk/chembl/glados_api/shared/properties_configuration/group' \
                              '/{index_name}/{group}/'


def run():
    """
    Runs the job
    """

    run_params = yaml.load(open(ARGS.run_params_file, 'r'), Loader=yaml.FullLoader)
    job_params = json.loads(run_params.get('job_params'))

    index_name = job_params.get('index_name')
    raw_query = job_params.get('query')
    desired_format = job_params.get('format')
    context_id = job_params.get('context_id')
    download_columns_group = job_params.get('download_columns_group', 'download')

    if context_id == 'null' or context_id == 'undefined':
        context_id = None

    if download_columns_group == 'null' or download_columns_group == 'undefined':
        download_columns_group = 'download'

    server_connection = job_utils.ServerConnection(run_params_file=ARGS.run_params_file, verbose=ARGS.verbose)
    make_download_file(index_name, raw_query, desired_format, context_id, download_columns_group)

    server_connection.update_job_status(job_utils.Statuses.RUNNING)
    server_connection.log('Execution Started')

    server_connection.update_job_status(job_utils.Statuses.FINISHED)
    server_connection.log('Everything OK!')


def make_download_file(index_name, raw_query, desired_format, context_id, download_columns_group):

    print('index_name:')
    print(index_name)

    print('raw_query:')
    print(raw_query)

    print('desired_format:')
    print(desired_format)

    print('context_id:')
    print(context_id)

    print('download_columns_group:')
    print(download_columns_group)

    columns_to_download = get_columns_to_download(index_name, download_columns_group)
    id_property = get_id_property_for_index(index_name)

    own_columns = [col for col in columns_to_download if col.get('is_contextual', False) is not True]


def get_columns_to_download(index_name, download_columns_group):

    columns_config_url = COLUMNS_CONFIG_URL_TEMPLATE.format(index_name=index_name, group=download_columns_group)
    columns_config_requests = requests.get(columns_config_url)
    config_got = columns_config_requests.json()
    return config_got['properties']['default']


def get_id_property_for_index(index_name):

    return 'molecule_chembl_id'

if __name__ == "__main__":
    run()
