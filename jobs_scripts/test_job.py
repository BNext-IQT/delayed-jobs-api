#!/usr/bin/env python3
"""
Script that runs a job to test the system
"""
import json
import argparse
import time
from pathlib import Path

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
    duration = job_params.get('seconds')
    instruction = job_params.get('instruction')

    server_connection = job_utils.ServerConnection(run_params_file=ARGS.run_params_file, verbose=ARGS.verbose)

    server_connection.update_job_status(job_utils.Statuses.RUNNING)
    server_connection.log('Execution Started')

    for i in range(1, duration + 1):
        time.sleep(1)
        progress = int((i / duration) * 100)
        server_connection.update_job_progress(progress)

    if instruction == 'FAIL':
        server_connection.update_job_status(job_utils.Statuses.ERROR)
        server_connection.log('I failed')
        return

    output_file_name = 'job_result.txt'
    with open(output_file_name, 'w') as out_file:
        out_file.write('Results Ready!')

    if instruction != 'DELETE_OUTPUT_FILE':
        server_connection.upload_job_results_file(str(Path(output_file_name).resolve()))

    server_connection.update_job_status(job_utils.Statuses.FINISHED)
    server_connection.log('Everything OK!')

if __name__ == "__main__":
    run()
