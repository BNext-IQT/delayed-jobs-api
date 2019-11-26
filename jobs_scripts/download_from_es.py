#!/usr/bin/env python3
"""
Script that collects data from elasctisearch and generates a file with it.
"""
import json
import argparse

import yaml

from common import job_utils

PARSER = argparse.ArgumentParser()
PARSER.add_argument('run_params_file', help='The path of the file with the run params')
PARSER.add_argument('-v', '--verbose', help='Make output verbose', action='store_true')
ARGS = PARSER.parse_args()


def run():
    """
    Runs the job
    """

    run_params = yaml.load(open(ARGS.run_params_file, 'r'), Loader=yaml.FullLoader)

    job_params = json.loads(run_params.get('job_params'))
    print('job_params:')
    print(json.dumps(job_params, indent=4))

    server_connection = job_utils.ServerConnection(run_params_file=ARGS.run_params_file, verbose=ARGS.verbose)

    server_connection.update_job_status(job_utils.Statuses.RUNNING)
    server_connection.log('Execution Started')

    server_connection.update_job_status(job_utils.Statuses.FINISHED)
    server_connection.log('Everything OK!')

if __name__ == "__main__":
    run()
