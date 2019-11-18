#!/usr/bin/env python3
import argparse
import yaml
import json
from common import job_utils
from urllib.parse import urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError
import requests
import time

parser = argparse.ArgumentParser()
parser.add_argument('run_params_file', help='The path of the file with the run params')
parser.add_argument('-v', '--verbose', help='Make output verbose', action="store_true")
parser.add_argument('-n', '--dry-run', help='Make output verbose', action='store_true', dest='dry_run')
args = parser.parse_args()

BLAST_API_BASE_URL = 'https://www.ebi.ac.uk/Tools/services/rest/ncbiblast'


class SearchError(Exception):
    """Base class for exceptions in this module."""
    pass


def run():

    run_params = yaml.load(open(args.run_params_file, 'r'), Loader=yaml.FullLoader)
    job_params = json.loads(run_params.get('job_params'))

    server_connection = job_utils.ServerConnection(run_params_file=args.run_params_file, verbose=args.verbose)
    server_connection.update_job_status(job_utils.Statuses.RUNNING)
    server_connection.log('Execution Started')

    print_if_verbose('job_params: ', json.dumps(job_params, indent=4))

    try:

        search_id = queue_blast_job(job_params)
        server_connection.log(f'Job successfully submitted to the EBI BLAST Service: {search_id}')
        job_status_url = f'https://www.ebi.ac.uk/Tools/services/web/toolresult.ebi?jobId={search_id}'
        print_if_verbose(job_status_url)
        server_connection.update_api_initial_url(job_status_url)

        search_finished = False
        while not search_finished:

            print_if_verbose('Going to check the search status')
            status, msg = get_blast_search_status(search_id)
            print_if_verbose(f'Search status: {status}; {msg}')
            server_connection.log(msg)

            if status == job_utils.Statuses.ERROR:
                server_connection.update_job_status(job_utils.Statuses.ERROR,
                                                    'Error while job was running on the EBI service')
                return

            if status == job_utils.Statuses.FINISHED:
                server_connection.log(msg)
                search_finished = True
            else:
                server_connection.update_job_status(status)

            time.sleep(1)

    except SearchError as e:
        error_msg = (str(e))
        server_connection.log(error_msg)
        server_connection.update_job_status(job_utils.Statuses.ERROR, error_msg)


def print_if_verbose(*print_args):
    if args.verbose:
        print(print_args)


def queue_blast_job(search_params):

    run_url = '{}/run/'.format(BLAST_API_BASE_URL)
    print_if_verbose('run_url: ', run_url)

    # add fixed chembl parameters
    search_params['stype'] = 'protein'
    search_params['program'] = 'blastp'
    search_params['database'] = 'chembl'
    search_params['email'] = 'chemblgroup@googlemail.com'

    print_if_verbose('search_params: ')
    print_if_verbose(search_params)

    request_data = urlencode(search_params)

    try:

        req = Request(run_url)
        req_handle = urlopen(req, request_data.encode(encoding=u'utf_8', errors=u'strict'))
        search_id = req_handle.read().decode(encoding=u'utf_8', errors=u'strict')
        req_handle.close()
        print_if_verbose('search_id: ', search_id)
        return search_id

    except HTTPError as ex:

        msg = 'Error while submitting BLAST job:\n{}'.format(repr(ex))
        print_if_verbose(msg)
        raise SearchError(msg)


def get_blast_search_status(search_id):

    status_url = '{}/status/{}'.format(BLAST_API_BASE_URL, search_id)
    r = requests.get(status_url)
    status_response = r.text

    if status_response == 'NOT_FOUND':
        status = job_utils.Statuses.ERROR
        msg = 'Search submission not found, it may have expired. Please run the search again.'
        return status, msg
    elif status_response == 'FAILURE':
        status = job_utils.Statuses.ERROR
        msg = 'There was an error in the EBI BLAST Search.'
        return status, msg
    elif status_response == 'RUNNING':
        status = job_utils.Statuses.RUNNING
        msg = 'Search is running...'
        return status, msg
    elif status_response == 'FINISHED':
        status = job_utils.Statuses.FINISHED
        msg = 'Search finished...'
        return status, msg
    else:
        status = job_utils.Statuses.ERROR
        msg = 'Response from the EBI service not recognised, please check manually.'
        return status, msg


if __name__ == "__main__":
    run()