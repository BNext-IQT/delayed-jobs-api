#!/usr/bin/env python3
import argparse
import time
import yaml
import datetime
import getpass
import socket
import requests
from enum import Enum
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('run_params_file', help='The path of the file with the run params')
parser.add_argument('-v', '--verbose', help='Make output verbose', action='store_true')
args = parser.parse_args()

RUN_PARAMS = {}
LOG = ''


class Statuses(Enum):
    """
    Possible Statuses
    """
    RUNNING = 'RUNNING'
    ERROR = 'ERROR'
    FINISHED = 'FINISHED'

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name


def run():
    global RUN_PARAMS
    RUN_PARAMS = yaml.load(open(args.run_params_file, 'r'), Loader=yaml.FullLoader)

    job_params = json.loads(RUN_PARAMS.get('job_params'))
    duration = job_params.get('seconds')
    instruction = job_params.get('instruction')

    update_job_status(Statuses.RUNNING)
    log('Execution Started')

    for i in range(1, duration + 1):
        time.sleep(1)
        progress = int((i / duration) * 100)
        update_job_progress(progress)

    if instruction == 'FAIL':
        update_job_status(Statuses.ERROR)
        log('I failed')
        return

    output_file_name = 'job_result.txt'
    with open(output_file_name, 'w') as out_file:
        out_file.write('Results Ready!')
        update_job_output_path(str(Path(output_file_name).resolve()))

    update_job_status(Statuses.FINISHED)
    log('Everything OK!')


def log(msg):
    """
    Same a message to the log
    :param msg: log message to save
    """
    global LOG
    username = getpass.getuser()
    hostname = socket.gethostname()

    full_msg = f'{username}@{hostname} [{datetime.datetime.utcnow()}]: {msg}\n'

    LOG += full_msg

    if args.verbose:
        print(full_msg)

    appended_status = {
        'log': LOG
    }
    send_status_update(appended_status)


def update_job_output_path(file_path):
    """
    Update's the job output file path
    :param file_path: the file path where the output is

    """
    if args.verbose:
        print('--------------------------------------------------------------------------------------')
        print('update_job_output_path: ', file_path)
        print('--------------------------------------------------------------------------------------')

    appended_status = {
        'output_file_path': file_path
    }
    send_status_update(appended_status)


def update_job_progress(progress_percentage):
    """
    Updates the job's progress percentage with the one given as parameter
    :param progress_percentage: current progress percentage
    :return:
    """
    if args.verbose:
        print('--------------------------------------------------------------------------------------')
        print('Setting progress percentage to', progress_percentage)
        print('--------------------------------------------------------------------------------------')

    appended_status = {
        'progress': progress_percentage
    }
    send_status_update(appended_status)


def update_job_status(new_status, status_comment=None):
    """
    Updates the job status
    :param new_status: new status that you want to save
    :param status_comment: a comment on the status. E.g. 'Loading ids'
    :return:
    """
    if args.verbose:
        print('--------------------------------------------------------------------------------------')
        print('Setting status to', str(new_status))
        print('--------------------------------------------------------------------------------------')

    appended_status = {
        'status': new_status,
        'status_comment': status_comment
    }

    send_status_update(appended_status)


def send_status_update(appended_status):
    """
    Sends the new status to the server via PATCH
    :param appended_status: dict with the new status to send
    """
    url = RUN_PARAMS.get('status_update_endpoint').get('url')
    job_token = RUN_PARAMS.get('job_token')
    headers = {
        'X-Job-Key': job_token
    }
    payload = appended_status

    if args.verbose:
        print('--------------------------------------------------------------------------------------')
        print('Sending status update')
        print('url: ', url)
        print('headers: ', headers)
        print('payload: ', payload)

    r = requests.patch(url, payload, headers=headers)

    if args.verbose:
        print('Server response: ', r.status_code)
        print('--------------------------------------------------------------------------------------')


if __name__ == "__main__":
    run()
