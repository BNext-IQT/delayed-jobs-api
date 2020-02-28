"""
This module submits jobs to the EBI queue
"""
import hashlib
import json
import os
import random
import shutil
import stat
import subprocess
from pathlib import Path
import re

import yaml

import app.app_logging as app_logging
from app.authorisation import token_generator
from app.config import RUN_CONFIG
from app.models import delayed_job_models

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

class JobSubmissionError(Exception):
    """Base class for exceptions in this module."""


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


def get_job_input_files_desc(args):
    """
    Saves the input files to a temporary directory to not depend from flask-respx implementation, then returns a
    structure describing them.
    :param args: files sent to the endpoint from flask
    :return: dict with the input files and their temporary location
    """

    input_files_desc = {}
    for param_key, parameter in args.items():
        tmp_dir = Path.joinpath(Path(JOBS_TMP_DIR), f'{random.randint(1, 1000000)}')
        os.makedirs(tmp_dir, exist_ok=True)
        tmp_path = Path.joinpath(Path(tmp_dir), parameter.filename)
        parameter.save(str(tmp_path))
        input_files_desc[param_key] = str(tmp_path)

    return input_files_desc


def parse_args_and_submit_job(job_type, form_args, file_args):

    docker_image_url = delayed_job_models.get_docker_image_url(job_type)
    job_params_only = {param_key: parameter for (param_key, parameter) in form_args.items()}
    job_inputs_only = get_job_input_files_desc(file_args)
    input_files_hashes = get_input_files_hashes(job_inputs_only)

    return submit_job(job_type, job_inputs_only, input_files_hashes, docker_image_url, job_params_only)


def submit_job(job_type, input_files_desc, input_files_hashes, docker_image_url, job_params):
    """
    Submits job to the queue, and runs it in background
    :param job_type: type of job to submit
    :param job_params: dict with the job parameters
    """

    try:

        # See if the job already exists
        job = delayed_job_models.get_job_by_params(job_type, job_params, docker_image_url, input_files_hashes)
        app_logging.info(f'Job {job.id} already exists')
        app_logging.info(f'job_params: {job_params}')
        must_ignore_cache = job_params.get('dl__ignore_cache', False)
        app_logging.info(f'must_ignore_cache: {must_ignore_cache}')
        if must_ignore_cache:
            app_logging.info(f'I was told to ignore cache so I will delete and submit again {job.id}')
            delayed_job_models.delete_job(job)
            job = create_and_submit_job(job_type, input_files_desc, input_files_hashes, docker_image_url, job_params)
            return get_job_submission_response(job)

        return get_job_submission_response(job)

    except delayed_job_models.JobNotFoundError:

        job = create_and_submit_job(job_type, input_files_desc, input_files_hashes, docker_image_url, job_params)
        return get_job_submission_response(job)


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

def create_and_submit_job(job_type, input_files_desc, input_files_hashes, docker_image_url, job_params):
    """
    Creates a job and submits if to LSF
    :param job_type: type of job to submit
    :param input_files_desc: dict with the paths of the input files
    :param input_files_hashes: dict with the hashes of the input files
    :param docker_image_url: image of the container to use
    :param job_params: parameters of the job
    :return: the job object created
    """
    job = delayed_job_models.get_or_create(job_type, job_params, docker_image_url, input_files_hashes)
    app_logging.info(f'Submitting Job: {job.id}')
    prepare_job_and_submit(job, input_files_desc)
    return job

def get_job_submission_response(job):
    """
    :param job: the job object for which get the submission response
    :return: a dict with the response of a submission
    """
    return {
        'job_id': job.id
    }

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


def get_job_run_params_file_path(job):
    """
    :param job: DelayedJob object
    :return: local path of the job run params file
    """
    return os.path.join(get_job_run_dir(job), RUN_PARAMS_FILENAME)


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
    submit_job_to_lsf(job)

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
            'url': f'http://{RUN_CONFIG.get("server_public_host")}'
                   f'{RUN_CONFIG.get("base_path", "")}/status/{job.id}',
            'method': 'PATCH'
        },
        'job_params': json.loads(job.raw_params)
    }


    run_params_path = get_job_run_params_file_path(job)

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

        lsf_config = RUN_CONFIG.get('lsf_submission')
        lsf_user = lsf_config['lsf_user']
        lsf_host = lsf_config['lsf_host']
        run_params_path = get_job_run_params_file_path(job)

        job_config = delayed_job_models.get_job_config(job.type)

        if (job_config.docker_registry_username is not None) and (job_config.docker_registry_password is not None):
            set_username = f"export SINGULARITY_DOCKER_USERNAME='{job_config.docker_registry_username}'"
            set_password = f"export SINGULARITY_DOCKER_PASSWORD='{job_config.docker_registry_password}'"
            set_docker_registry_credentials = f'{set_username}\n{set_password}\n'
        else:
            set_docker_registry_credentials = ''

        job_submission_script = submit_job_template.format(
            JOB_ID=job.id,
            LSF_USER=lsf_user,
            LSF_HOST=lsf_host,
            RUN_PARAMS_FILE=run_params_path,
            DOCKER_IMAGE_URL=job.docker_image_url,
            SET_DOCKER_REGISTRY_CREDENTIALS=set_docker_registry_credentials,
            RUN_DIR=get_job_run_dir(job)

        )
        job.lsf_host = lsf_host
        delayed_job_models.save_job(job)

        submit_file_path = get_job_submission_script_file_path(job)
        with open(submit_file_path, 'w') as submission_script_file:
            submission_script_file.write(job_submission_script)

        # make sure file is executable
        file_stats = os.stat(submit_file_path)
        os.chmod(submit_file_path, file_stats.st_mode | stat.S_IEXEC)


# ----------------------------------------------------------------------------------------------------------------------
# Job submission
# ----------------------------------------------------------------------------------------------------------------------
def submit_job_to_lsf(job):
    """
    Runs a script that submits the job to LSF
    :param job: DelayedJob object
    """
    submit_file_path = get_job_submission_script_file_path(job)
    submission_output_path = Path(submit_file_path).parent.joinpath('submission.out')
    submission_error_path = Path(submit_file_path).parent.joinpath('submission.err')

    lsf_config = RUN_CONFIG.get('lsf_submission')
    id_rsa_path = lsf_config['id_rsa_file']

    run_command = f'{submit_file_path} {id_rsa_path}'
    app_logging.info(f'Going to run job submission script, command: {run_command}')

    must_run_jobs = RUN_CONFIG.get('run_jobs', True)
    if not must_run_jobs:
        app_logging.info(f'Not submitting jobs because run_jobs is False')
        return

    submission_process = subprocess.run(run_command.split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    app_logging.info(f'Output: \n {submission_process.stdout}')
    app_logging.info(f'Error: \n {submission_process.stderr}')

    with open(submission_output_path, 'wb') as submission_out_file:
        submission_out_file.write(submission_process.stdout)

    with open(submission_error_path, 'wb') as submission_err_file:
        submission_err_file.write(submission_process.stderr)

    return_code = submission_process.returncode
    app_logging.info(f'submission return code was: {return_code}')
    if return_code != 0:
        raise JobSubmissionError('There was an error when running the job submission script! Please check the logs')

    lsf_job_id = get_lsf_job_id(str(submission_process.stdout))
    job.lsf_job_id = lsf_job_id
    delayed_job_models.save_job(job)
    app_logging.info(f'LSF Job ID is: {lsf_job_id}')


def get_lsf_job_id(submission_out):
    """
    Reads the output of the job submission command and returns the lsf job id assigned
    :param submission_out: the output of the submission command
    :return: the lsf job id
    """
    match = re.search(r'Job <\d+>', submission_out)
    job_id = re.split(r'<|>', match.group(0))[1]

    return int(job_id)





