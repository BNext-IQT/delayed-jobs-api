#!/usr/bin/env python3
import argparse
import time
import yaml
import json
from pathlib import Path
import os
from common import job_utils

parser = argparse.ArgumentParser()
parser.add_argument('run_params_file', help='The path of the file with the run params')
parser.add_argument('-v', '--verbose', help='Make output verbose', action='store_true')
args = parser.parse_args()

RUN_PARAMS = {}


def run():
    global RUN_PARAMS
    RUN_PARAMS = yaml.load(open(args.run_params_file, 'r'), Loader=yaml.FullLoader)

    job_params = json.loads(RUN_PARAMS.get('job_params'))
    duration = job_params.get('seconds')
    instruction = job_params.get('instruction')

    server_base_url = RUN_PARAMS.get('status_update_endpoint').get('url')
    job_token = RUN_PARAMS.get('job_token')

    server_connection = job_utils.ServerConnection(server_base_url=server_base_url,
                                                   job_token=job_token,
                                                   verbose=args.verbose)

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
        server_connection.update_job_output_path(str(Path(output_file_name).resolve()))

    if instruction == 'DELETE_OUTPUT_FILE':
        full_output_path = str(Path(output_file_name).resolve())
        print('DELETING OUTPUT FILE: ', full_output_path)
        os.remove(full_output_path)

        server_connection.update_job_status(job_utils.Statuses.FINISHED)
    server_connection.log('Everything OK!')

if __name__ == "__main__":
    run()
