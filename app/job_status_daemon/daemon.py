"""
Module that implements the daemon that checks the statuses of jobs in LSF
"""
import os
from pathlib import Path
import socket
import datetime
import stat
import subprocess
import re
import json
import random

from app.models import delayed_job_models
from app.config import RUN_CONFIG
from app.blueprints.job_submission.services import job_submission_service
from app.job_status_daemon import locks

DEFAULT_SLEEP_TIME = 1

AGENT_RUN_DIR = RUN_CONFIG.get('status_agent_run_dir', str(Path().absolute()) + '/status_agents_run')
if not os.path.isabs(AGENT_RUN_DIR):
    AGENT_RUN_DIR = Path(AGENT_RUN_DIR).resolve()
os.makedirs(AGENT_RUN_DIR, exist_ok=True)

class JobStatusDaemonError(Exception):
    """Base class for exceptions in this module."""

print('------------------------------------------------------------------------------')
print(f'AGENT_RUN_DIR: {AGENT_RUN_DIR}')
print('------------------------------------------------------------------------------')

def check_jobs_status(delete_lock_after_finishing=True):
    """
    The main function of this module. Checks for jobs to check the status, and checks their status in lsf
    :param delete_lock_after_finishing: determines if explicitly deletes the lock after finishing
    :return: (sleeptime, jobs_were_checked) the amount of seconds to wait for the next run and if the jobs
    were checked or not
    """
    lsf_config = RUN_CONFIG.get('lsf_submission')
    current_lsf_host = lsf_config['lsf_host']
    my_hostname = socket.gethostname()

    existing_lock = locks.get_lock_for_lsf_host(current_lsf_host)
    if existing_lock is not None:

        sleep_time = DEFAULT_SLEEP_TIME + random.random()
        print(f'I ({my_hostname}) found a lock, waiting {sleep_time} seconds before checking again')
        return sleep_time, False

    else:
        print(f'Locking LSF status check for {current_lsf_host}, I am {my_hostname}')
        locks.set_lsf_lock(current_lsf_host, my_hostname)

    print('Looking for jobs to check...')
    lsf_job_ids_to_check = get_lsf_job_ids_to_check()
    print(f'lsf_job_ids_to_check: {lsf_job_ids_to_check}')

    if len(lsf_job_ids_to_check) == 0:
        return DEFAULT_SLEEP_TIME, True

    script_path = prepare_job_status_check_script(lsf_job_ids_to_check)
    must_run_script = RUN_CONFIG.get('run_status_script', True)
    if not must_run_script:
        print('Not running script because run_status_script is False')
        return DEFAULT_SLEEP_TIME, False

    try:
        script_output = get_status_script_output(script_path)
        os.remove(script_path)  # Remove the script after running so it doesn't fill up the NFS
        print(f'deleted script: {script_path}')
        parse_bjobs_output(script_output)
        return DEFAULT_SLEEP_TIME, True
    except JobStatusDaemonError as error:
        print(error)

def get_lsf_job_ids_to_check():
    """
    :return: a list of LSF job IDs for which it is necessary check the status in the LSF cluster. The jobs that are
    checked are the ones that:
    1. Were submitted to the same LSF cluster that I am running with (defined in configuration)
    2. Are not in Error or Finished state.
    """

    lsf_config = RUN_CONFIG.get('lsf_submission')
    lsf_host = lsf_config['lsf_host']

    return delayed_job_models.get_lsf_job_ids_to_check(lsf_host)

def get_check_job_status_script_path():
    """
    :return: the path to use for creating the job status script
    """

    filename = f'{datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}_check_lsf_job_status.sh'
    job_status_check_script_path = Path(AGENT_RUN_DIR).joinpath(socket.gethostname(), filename)

    return job_status_check_script_path

# ----------------------------------------------------------------------------------------------------------------------
# Preparing status script
# ----------------------------------------------------------------------------------------------------------------------
def prepare_job_status_check_script(lsf_job_ids):
    """
    Prepares the script that will check for the job status to LSF
    :lsf_job_ids: the list of job ids for which check the status
    :return: the final path of the script that was created
    """

    job_status_script_template_path = os.path.join(Path().absolute(), 'templates', 'get_jobs_status.sh')
    with open(job_status_script_template_path, 'r') as template_file:
        job_status_template = template_file.read()

        lsf_config = RUN_CONFIG.get('lsf_submission')
        lsf_user = lsf_config['lsf_user']
        lsf_host = lsf_config['lsf_host']

        job_submission_script = job_status_template.format(
            LSF_JOB_IDS=' '.join([str(lsf_job_id) for lsf_job_id in lsf_job_ids]),
            LSF_USER=lsf_user,
            LSF_HOST=lsf_host
        )

        status_script_path = get_check_job_status_script_path()
        status_script_path.parent.mkdir(parents=True, exist_ok=True)
        with open(status_script_path, 'w') as status_script_file:
            status_script_file.write(job_submission_script)

        print(f'created script: {status_script_path}')
        # make sure file is executable
        file_stats = os.stat(status_script_path)
        os.chmod(status_script_path, file_stats.st_mode | stat.S_IEXEC)

    return status_script_path

# ----------------------------------------------------------------------------------------------------------------------
# Parsing status script output
# ----------------------------------------------------------------------------------------------------------------------
def get_status_script_output(script_path):
    """
    Runs the status script and returns a text with the output obtained, if there is an error raises an exception
    :param script_path: path of the script
    :return: the text output of stdout
    """
    lsf_config = RUN_CONFIG.get('lsf_submission')
    id_rsa_path = lsf_config['id_rsa_file']
    run_command = f'{script_path} {id_rsa_path}'
    print(f'Going to run job status script, command: {run_command}')
    status_check_process = subprocess.run(run_command.split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    print(f'Output: \n {status_check_process.stdout}')
    print(f'Error: \n {status_check_process.stderr}')

    return_code = status_check_process.returncode
    print(f'script return code was: {return_code}')

    if return_code != 0:

        status_output_path = f'{script_path}.out'
        status_error_path = f'{script_path}.err'

        with open(status_output_path, 'wb') as status_out_file:
            status_out_file.write(status_check_process.stdout)

        with open(status_error_path, 'wb') as status_err_file:
            status_err_file.write(status_check_process.stderr)

        raise JobStatusDaemonError('There was an error when running the job status script! Please check the logs')
    else:
        return status_check_process.stdout.decode()

def parse_bjobs_output(script_output):
    """
    parses the output passed as parameter. Modifies the status of the job in the database accordingly
    :param script_output: string output of the script that requests the status of the job
    """

    match = re.search(r'START_REMOTE_SSH[\s\S]*FINISH_REMOTE_SSH', script_output)
    bjobs_output_str = re.split(r'(START_REMOTE_SSH\n|\nFINISH_REMOTE_SSH)', match.group(0))[2]

    try:
        json_output = json.loads(bjobs_output_str)
        react_to_bjobs_json_output(json_output)
    except json.decoder.JSONDecodeError as error:
        print(f'unable to decode output. Will try again later anyway {error}')

def react_to_bjobs_json_output(json_output):
    """
    Reads the dict obtained from the status script output, modifies the jobs accordingly
    :param json_output: dict with the output parsed from running the command
    """
    for record in json_output['RECORDS']:
        lsf_id = record['JOBID']
        lsf_status = record['STAT']
        new_status = map_lsf_status_to_job_status(lsf_status)
        job = delayed_job_models.get_job_by_lsf_id(lsf_id)

        old_status = job.status
        status_changed = old_status != new_status
        if not status_changed:
            continue

        job.status = new_status
        if new_status == delayed_job_models.JobStatuses.RUNNING:

            parse_job_started_at_time_if_not_set(job, record)

        elif new_status == delayed_job_models.JobStatuses.ERROR:

            # If the job ran too fast, the started at could have not been captured by my previous run.
            parse_job_started_at_time_if_not_set(job, record)
            parse_job_finished_at_time_if_not_set(job, record)
            if job.num_failures is None:
                job.num_failures = 0
            job.num_failures += 1

        elif new_status == delayed_job_models.JobStatuses.FINISHED:

            parse_job_started_at_time_if_not_set(job, record)
            parse_job_finished_at_time_if_not_set(job, record)
            save_job_outputs(job)

        delayed_job_models.save_job(job)
        print(f'Job {job.id} with lsf id {job.lsf_job_id} new state is {new_status}')


def parse_job_started_at_time_if_not_set(job, lsf_record):
    """
    saves the started at time of the job from the lsf record obtained if it was not set before
    :param job: job object to which save the started at time
    :param lsf_record: record obtained from bjobs output
    """
    if job.started_at is None:
        lsf_date_str = lsf_record['START_TIME']
        started_at = parse_bjobs_output_date(lsf_date_str)
        job.started_at = started_at
        print(f'Job {job.id} started at time is {started_at}')


def parse_job_finished_at_time_if_not_set(job, lsf_record):
    """
    saves the started at time of the job from the lsf record obtained if it was not set before
    :param job: job object to which save the started at time
    :param lsf_record: record obtained from bjobs output
    """
    if job.finished_at is None:
        lsf_date_str = lsf_record['FINISH_TIME']
        finished_at = parse_bjobs_output_date(lsf_date_str)
        job.finished_at = finished_at
        print(f'Job {job.id} finished at time is {finished_at}')


def map_lsf_status_to_job_status(lsf_status):
    """
    maps the lsf status to a status defined in models
    :param lsf_status: status obtained from lsf
    :return: one of the status defined in the delayed_jobs_models module
    """
    if lsf_status == 'RUN':
        return delayed_job_models.JobStatuses.RUNNING
    elif lsf_status == 'PEND':
        return delayed_job_models.JobStatuses.QUEUED
    elif lsf_status == 'EXIT':
        return delayed_job_models.JobStatuses.ERROR
    elif lsf_status == 'DONE':
        return delayed_job_models.JobStatuses.FINISHED
    else:
        return delayed_job_models.JobStatuses.UNKNOWN

def parse_bjobs_output_date(lsf_date_str):
    """
    Parses the data obtained by the date provided by the bjobs output
    :param lsf_date_str: the string received from bjobs
    :return: a python datetime representing the date parsed
    """
    # Just return current date, to avoid date parsing issues. LSF is not responding to the -hms parameter
    return datetime.datetime.now(tz=datetime.timezone.utc)

def save_job_outputs(job):
    """
    Lists the files of the output dir of the job and saves the corresponding output objects
    :param job: job that is finished
    """
    job_outputs_dir = job.output_dir_path

    paths_list = []
    append_files_in_dir(job_outputs_dir, paths_list)

    for absolute_path in paths_list:
        relative_path = absolute_path.replace(f'{job_submission_service.JOBS_OUTPUT_DIR}/', '', 1)
        output_url = get_output_file_url(relative_path)
        delayed_job_models.add_output_to_job(job, absolute_path, output_url)
        print(f'Added output file {absolute_path} with url {output_url} to job {job.id}')


def append_files_in_dir(path, paths_list):
    """
    Appends to the lists all the paths of the files in path and subdirectories recursively
    :param path: base directory for which to list the files
    :param paths_list: list where to accumulate the paths
    """
    for item in os.listdir(path):
        abs_path = Path(path).joinpath(item).resolve()
        if os.path.isfile(abs_path):
            paths_list.append(str(abs_path))
        else:
            append_files_in_dir(abs_path, paths_list)

def get_output_file_url(file_relative_path):
    """
    :param file_relative_path: the relative path from the job outputs dir.
    For example: Job-1/subdir/output_0.txt
    :return: the url of an output file given a path from the job outputs dir
    """
    server_name = RUN_CONFIG.get("server_public_host")

    server_base_path = RUN_CONFIG.get('base_path', '')
    if server_base_path == '':
        server_base_path_with_slash = ''
    else:
        server_base_path_with_slash = f'{server_base_path}/'
        if server_base_path_with_slash.startswith('//'):
            server_base_path_with_slash = server_base_path_with_slash[1:]
        if server_base_path_with_slash.endswith('/'):
            server_base_path_with_slash = server_base_path_with_slash[:-1]

    outputs_base_path = RUN_CONFIG.get('outputs_base_path')

    return f'{server_name}{server_base_path_with_slash}/{outputs_base_path}/{file_relative_path}'


