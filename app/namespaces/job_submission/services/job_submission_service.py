"""
This module submits jobs to the EBI queue
"""
from pathlib import Path
import os
import stat
import shutil
import subprocess
import socket
import hashlib
import random
import json

import werkzeug
import yaml

from app.namespaces.models import delayed_job_models
from app.config import RUN_CONFIG
from app.authorisation import token_generator
import app.app_logging as app_logging

JOBS_RUN_DIR = RUN_CONFIG.get('jobs_run_dir', str(Path().absolute()) + '/jobs_run')
if not os.path.isabs(JOBS_RUN_DIR):
    JOBS_RUN_DIR = Path(JOBS_RUN_DIR).resolve()
os.makedirs(JOBS_RUN_DIR, exist_ok=True)

JOBS_TMP_DIR = RUN_CONFIG.get('jobs_tmp_dir', str(Path().absolute()) + '/jobs_tmp_dir')
if not os.path.isabs(JOBS_TMP_DIR):
    JOBS_TMP_DIR = Path(JOBS_TMP_DIR).resolve()
os.makedirs(JOBS_TMP_DIR, exist_ok=True)

JOBS_OUTPUT_DIR = RUN_CONFIG.get('jobs_output_dir', str(Path().absolute()) + '/jobs_output')
if not os.path.isabs(JOBS_OUTPUT_DIR):
    JOBS_OUTPUT_DIR = Path(JOBS_OUTPUT_DIR).resolve()
os.makedirs(JOBS_OUTPUT_DIR, exist_ok=True)

app_logging.info('------------------------------------------------------------------------------')
app_logging.info(f'JOBS_RUN_DIR: {JOBS_RUN_DIR}')
app_logging.info('------------------------------------------------------------------------------')

app_logging.info('------------------------------------------------------------------------------')
app_logging.info(f'JOBS_OUTPUT_DIR: {JOBS_OUTPUT_DIR}')
app_logging.info('------------------------------------------------------------------------------')

JOBS_SCRIPTS_DIR = str(Path().absolute()) + '/jobs_scripts'

INPUT_FILES_DIR_NAME = 'input_files'
RUN_PARAMS_FILENAME = 'run_params.yml'
COMMON_PACKAGE_NAME = 'common'
SUBMISSION_FILE_NAME = 'submit_job.sh'

MAX_RETRIES = 6

def get_input_files_hashes(input_files_desc):
    """
    :param input_files_desc: args sent to the endpoint from flask rest-plus
    :return: dict with the hashes of each of the files uploaded as an input
    """

    input_files_hashes = {}
    for input_key, input_path in input_files_desc.items():
        with open(input_path, 'rb') as input_file:
            file_bytes = input_file.read()
            file_hash = hashlib.sha256(file_bytes).hexdigest()
            input_files_hashes[input_key] = file_hash

    return input_files_hashes


def get_job_input_files_desc_only(args):
    """
    Saves the input files to a temporary directory to not depend from flask-respx implementation, then returns a
    structure describing them.
    :param args: args sent to the endpoint from flask rest-plus
    :return: dict with the input files and their temporary location
    """

    input_files_desc = {}
    for param_key, parameter in args.items():
        if isinstance(parameter, werkzeug.datastructures.FileStorage):
            tmp_dir = Path.joinpath(Path(JOBS_TMP_DIR), f'{random.randint(1, 1000000)}')
            os.makedirs(tmp_dir, exist_ok=True)
            tmp_path = Path.joinpath(Path(tmp_dir), parameter.filename)
            parameter.save(str(tmp_path))
            input_files_desc[param_key] = str(tmp_path)

    return input_files_desc


def get_job_params_only(args):
    """
    :param args: args sent to the endpoint from flask rest-plus
    :return: dict the parameters that are not files
    """
    job_params = {}
    for param_key, parameter in args.items():
        if not isinstance(parameter, werkzeug.datastructures.FileStorage):
            job_params[param_key] = parameter

    return job_params


def parse_args_and_submit_job(job_type, args):

    job_params_only = get_job_params_only(args)
    job_inputs_only = get_job_input_files_desc_only(args)
    input_files_hashes = get_input_files_hashes(job_inputs_only)

    return submit_job(job_type, job_inputs_only, input_files_hashes, job_params_only)


def submit_job(job_type, input_files_desc, input_files_hashes, job_params):
    """
    Submits job to the queue, and runs it in background
    :param job_type: type of job to submit
    :param job_params: dict with the job parameters
    """

    job = delayed_job_models.get_or_create(job_type, job_params, input_files_hashes)
    app_logging.info(f'Submitting Job: {job.id}')
    prepare_job_and_submit(job, input_files_desc)

    return job.public_dict()

    return
    try:
        # See if the job existed before
        job = delayed_job_models.get_job_by_params(job_type, job_params)

        if job.status == delayed_job_models.JobStatuses.ERROR:
            if job.get_executions_count() < (MAX_RETRIES + 1):
                prepare_job_and_run(job)

        job_status = job.status
        output_file_path = job.output_file_path
        results_file_is_not_accessible = (output_file_path is None) or (not os.path.exists(output_file_path))
        if (job_status == delayed_job_models.JobStatuses.FINISHED) and results_file_is_not_accessible:
            prepare_job_and_run(job)

    except delayed_job_models.JobNotFoundError:
        # It doesn't exist, so I submit it


        job = delayed_job_models.get_or_create(job_type, job_params)
        prepare_job_and_run(job)

    return job.public_dict()


def get_job_run_dir(job):
    """
    :param job: DelayedJob object
    :return: run dir of the job
    """
    return os.path.join(JOBS_RUN_DIR, job.id)


def get_job_input_files_dir(job):
    """
    :param job: DelayedJob object
    :return: input files dir of the job
    """
    return os.path.join(get_job_run_dir(job), INPUT_FILES_DIR_NAME)


def get_job_submission_script_file_path(job):
    """
    :param job: DelayedJob object
    :return: local path of the job results file
    """
    return os.path.join(get_job_run_dir(job), SUBMISSION_FILE_NAME)


def get_job_output_dir_path(job):
    """
    :param job: DelayedJob object
    :return: local path to place the results file of a job
    """
    return os.path.join(JOBS_OUTPUT_DIR, job.id)


def prepare_job_and_submit(job, input_files_desc):
    """
    prepares the run directory of the job, then executes the job script as a suprpocess
    :param job: DelayedJob object
    :param input_files_desc: a dict describing the input files and their temporary location
    """
    prepare_run_folder(job, input_files_desc)
    prepare_output_dir(job)
    prepare_job_submission_script(job)

    must_run_jobs = RUN_CONFIG.get('run_jobs', True)
    # if must_run_jobs:
    #     run_job(job)

# ----------------------------------------------------------------------------------------------------------------------
# Preparation of run folder
# ----------------------------------------------------------------------------------------------------------------------
# pylint: disable=too-many-locals
def prepare_run_folder(job, input_files_desc):
    """
    Prepares the folder where the job will run
    :param job: DelayedJob object
    """

    create_job_run_dir(job)
    create_params_file(job, input_files_desc)

def create_job_run_dir(job):
    """
    CReates the directory where the job will run
    :param job: job object for which to create the job run directory
    """
    job_run_dir = get_job_run_dir(job)
    job_input_files_dir = get_job_input_files_dir(job)

    if os.path.exists(job_run_dir):
        shutil.rmtree(job_run_dir)

    job.run_dir_path = job_run_dir
    delayed_job_models.save_job(job)
    os.makedirs(job_run_dir, exist_ok=True)
    os.makedirs(job_input_files_dir, exist_ok=True)

    app_logging.info(f'Job run dir is {job_run_dir}')

def create_params_file(job, input_files_desc):
    """
    Creates the parameters file for the job
    :param job: job oject for which the parmeters file will be created
    """
    job_token = token_generator.generate_job_token(job.id)

    run_params = {
        'job_id': job.id,
        'job_token': job_token,
        'inputs': prepare_job_inputs(job, input_files_desc),
        'output_dir': get_job_output_dir_path(job),
        'status_update_endpoint': {
            'url': f'http://127.0.0.1:5000{RUN_CONFIG.get("base_path", "")}/status/{job.id}',
            'method': 'PATCH'
        },
        'job_params': json.loads(job.raw_params)
    }


    run_params_path = os.path.join(get_job_run_dir(job), RUN_PARAMS_FILENAME)

    # delete file if existed before, just in case
    if os.path.exists(run_params_path):
        os.remove(run_params_path)

    with open(run_params_path, 'w') as out_file:
        out_file.write(yaml.dump(run_params))


def prepare_job_inputs(job, tmp_input_files_desc):
    """
    Moves the input files from the temporary folder to its proper run folder. Deletes the temporary files. Returns a
    dictionary describing the input files.
    :param job: job object for which the input files are prepared
    :param tmp_input_files_desc: dict describing the temporary path
    """
    input_files_desc = {}
    tmp_parent_dir = None

    for key, tmp_path in tmp_input_files_desc.items():
        filename = Path(tmp_path).name
        run_path = Path(get_job_input_files_dir(job)).joinpath(filename)
        shutil.move(tmp_path, run_path)
        tmp_parent_dir = Path(tmp_path).parent
        input_files_desc[key] = str(run_path)

    if tmp_parent_dir is not None:
        shutil.rmtree(tmp_parent_dir)

    return input_files_desc

def prepare_output_dir(job):
    """
    Makes sure to create the output dir for the job
    :param job: job object for which create the job output
    """

    job_output_dir = get_job_output_dir_path(job)

    if os.path.exists(job_output_dir):
        shutil.rmtree(job_output_dir)

    job.output_dir_path = job_output_dir
    delayed_job_models.save_job(job)
    os.makedirs(job_output_dir, exist_ok=True)

    app_logging.info(f'Job output dir is {job_output_dir}')

def prepare_job_submission_script(job):
    """
    Prepares the script that will submit the job to LSF
    :param job: job object for which prepare the job submission script
    """

    job_submission_script_template_path = os.path.join(Path().absolute(), 'templates', SUBMISSION_FILE_NAME)
    with open(job_submission_script_template_path, 'r') as template_file:
        submit_job_template = template_file.read()
        job_submission_script = submit_job_template.format(JOB_ID=job.id)

        submit_file_path = get_job_submission_script_file_path(job)
        with open(submit_file_path, 'w') as submission_script_file:
            submission_script_file.write(job_submission_script)

        # make sure file is executable
        file_stats = os.stat(submit_file_path)
        os.chmod(submit_file_path, file_stats.st_mode | stat.S_IEXEC)


def run_job(job):
    """
    Runs the job in background by executing the run script
    :param job: DelayedJob object
    """

    run_command = f'{get_job_run_file_path(job)}'
    run_output = subprocess.Popen([run_command, '&'])

    job_execution = delayed_job_models.JobExecution(
        hostname=socket.gethostname(),
        command=run_command,
        pid=run_output.pid,
        run_dir=get_job_run_dir(job)
    )

    delayed_job_models.add_job_execution_to_job(job, job_execution)