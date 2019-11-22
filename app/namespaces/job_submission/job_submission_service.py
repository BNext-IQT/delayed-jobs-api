"""
This module submits jobs to the EBI queue
"""
from pathlib import Path
import os
import stat
import shutil
import subprocess
import socket

from app.namespaces.models import delayed_job_models
from app.config import RUN_CONFIG
from app.authorisation import token_generator

JOBS_RUN_DIR = RUN_CONFIG.get('jobs_run_dir')
if JOBS_RUN_DIR is None:
    JOBS_RUN_DIR = str(Path().absolute()) + '/jobs_run'
if not os.path.isabs(JOBS_RUN_DIR):
    JOBS_RUN_DIR = Path(JOBS_RUN_DIR).resolve()
os.makedirs(JOBS_RUN_DIR, exist_ok=True)

JOBS_OUTPUT_DIR = RUN_CONFIG.get('jobs_output_dir')
if JOBS_OUTPUT_DIR is None:
    JOBS_OUTPUT_DIR = str(Path().absolute()) + '/jobs_output'
if not os.path.isabs(JOBS_OUTPUT_DIR):
    JOBS_OUTPUT_DIR = Path(JOBS_OUTPUT_DIR).resolve()
os.makedirs(JOBS_OUTPUT_DIR, exist_ok=True)

print('------------------------------------------------------------------------------')
print('JOBS_RUN_DIR: ', JOBS_RUN_DIR)
print('------------------------------------------------------------------------------')

print('------------------------------------------------------------------------------')
print('JOBS_OUTPUT_DIR: ', JOBS_OUTPUT_DIR)
print('------------------------------------------------------------------------------')

JOBS_SCRIPTS_DIR = str(Path().absolute()) + '/jobs_scripts'

RUN_PARAMS_FILENAME = 'run_params.yml'
RUN_FILE_NAME = 'run.sh'
COMMON_PACKAGE_NAME = 'common'

SCRIPT_FILENAMES = {
    f'{delayed_job_models.JobTypes.TEST}': 'test_job.py',
    f'{delayed_job_models.JobTypes.SIMILARITY}': 'structure_search.py',
    f'{delayed_job_models.JobTypes.SUBSTRUCTURE}': 'structure_search.py',
    f'{delayed_job_models.JobTypes.CONNECTIVITY}': 'structure_search.py',
    f'{delayed_job_models.JobTypes.BLAST}': 'blast_search.py'
}

UTILS_PACKAGE_PATH = os.path.join(JOBS_SCRIPTS_DIR, COMMON_PACKAGE_NAME)

SCRIPT_FILES = {
    f'{delayed_job_models.JobTypes.TEST}':
        os.path.join(JOBS_SCRIPTS_DIR, SCRIPT_FILENAMES.get(str(delayed_job_models.JobTypes.TEST))),
    f'{delayed_job_models.JobTypes.SIMILARITY}':
        os.path.join(JOBS_SCRIPTS_DIR, SCRIPT_FILENAMES.get(str(delayed_job_models.JobTypes.SIMILARITY))),
    f'{delayed_job_models.JobTypes.SUBSTRUCTURE}':
        os.path.join(JOBS_SCRIPTS_DIR, SCRIPT_FILENAMES.get(str(delayed_job_models.JobTypes.SUBSTRUCTURE))),
    f'{delayed_job_models.JobTypes.CONNECTIVITY}':
        os.path.join(JOBS_SCRIPTS_DIR, SCRIPT_FILENAMES.get(str(delayed_job_models.JobTypes.CONNECTIVITY))),
    f'{delayed_job_models.JobTypes.BLAST}':
        os.path.join(JOBS_SCRIPTS_DIR, SCRIPT_FILENAMES.get(str(delayed_job_models.JobTypes.BLAST))),
}

MAX_RETRIES = 6


def submit_job(job_type, job_params):
    """
    Submits job to the queue, and runs it in background
    :param job_type: type of job to submit
    :param job_params: dict with the job parameters
    """

    try:
        job = delayed_job_models.get_job_by_params(job_type, job_params)

        if job.status == delayed_job_models.JobStatuses.ERROR:
            if job.get_executions_count() < (MAX_RETRIES + 1):
                prepare_job_and_run(job)

        # This will not be necessary if we get FIRE
        job_status = job.status
        output_file_path = job.output_file_path
        results_file_is_not_accessible = (output_file_path is None) or (not os.path.exists(output_file_path))
        if (job_status == delayed_job_models.JobStatuses.FINISHED) and results_file_is_not_accessible:
            prepare_job_and_run(job)

    except delayed_job_models.JobNotFoundError:
        job = delayed_job_models.get_or_create(job_type, job_params)
        prepare_job_and_run(job)

    return job.public_dict()


def get_job_run_dir(job):
    """
    :param job: DelayedJob object
    :return: run dir of the job
    """
    return os.path.join(JOBS_RUN_DIR, job.id)


def get_job_run_file_path(job):
    """
    :param job: DelayedJob object
    :return: local path of the job results file
    """
    return os.path.join(get_job_run_dir(job), RUN_FILE_NAME)


def get_job_output_dir_path(job):
    """
    :param job: DelayedJob object
    :return: local path to place the results file of a job
    """
    return os.path.join(JOBS_OUTPUT_DIR, job.id)


def prepare_job_and_run(job):
    """
    prepares the run directory of the job, then executes the job script as a suprpocess
    :param job: DelayedJob object
    """
    job.output_dir_path = get_job_output_dir_path(job)
    prepare_run_folder(job)
    must_run_jobs = RUN_CONFIG.get('run_jobs', True)
    if must_run_jobs:
        run_job(job)


# pylint: disable=too-many-locals
def prepare_run_folder(job):
    """
    Prepares the folder where the job will run
    :param job: DelayedJob object
    """

    job_run_dir = get_job_run_dir(job)

    if os.path.exists(job_run_dir):
        shutil.rmtree(job_run_dir)

    job.run_dir_path = job_run_dir
    delayed_job_models.save_job(job)
    os.makedirs(job_run_dir, exist_ok=True)

    template_run_params_path = os.path.join(Path().absolute(), 'templates', 'run_params_template.yml')
    template_file = open(template_run_params_path, 'r')
    run_params_template = template_file.read()
    template_file.close()
    job_token = token_generator.generate_job_token(job.id)

    run_params = run_params_template.format(
        JOB_ID=job.id,
        JOB_TOKEN=job_token,
        STATUS_UPDATE_URL=f'http://127.0.0.1:5000/status/{job.id}',
        STATUS_UPDATE_METHOD='PATCH',
        STATISTICS_URL=f'http://127.0.0.1:5000/record/search/{job.id}',
        STATISTICS_METHOD='POST',
        FILE_UPLOAD_URL=f'http://127.0.0.1:5000/status/{job.id}/results_file',
        FILE_UPLOAD_METHOD='POST',
        JOB_PARAMS=f'{job.raw_params}',
    )

    run_params_path = os.path.join(job_run_dir, RUN_PARAMS_FILENAME)

    # delete file if existed before, just in case
    if os.path.exists(run_params_path):
        os.remove(run_params_path)

    with open(run_params_path, 'w') as out_file:
        out_file.write(run_params)

    job_script = SCRIPT_FILES[str(job.type)]
    script_path = os.path.join(job_run_dir, SCRIPT_FILENAMES[str(job.type)])
    shutil.copyfile(job_script, script_path)

    shutil.copytree(UTILS_PACKAGE_PATH, os.path.join(job_run_dir, COMMON_PACKAGE_NAME))

    # make sure file is executable
    file_stats = os.stat(script_path)
    os.chmod(script_path, file_stats.st_mode | stat.S_IEXEC)

    run_job_template_file = open(os.path.join(Path().absolute(), 'templates', RUN_FILE_NAME))
    run_job_template = run_job_template_file.read()
    run_job_params = run_job_template.format(
        RUN_DIR=job_run_dir,
        SCRIPT_TO_EXECUTE=script_path,
        PARAMS_FILE=run_params_path
    )
    run_job_template_file.close()
    run_file_path = get_job_run_file_path(job)

    with open(run_file_path, 'w') as out_file:
        out_file.write(run_job_params)

    # make sure file is executable
    file_stats = os.stat(run_file_path)
    os.chmod(run_file_path, file_stats.st_mode | stat.S_IEXEC)


def run_job(job):
    """
    Runs the job in background by executing the run script
    :param job: DelayedJob object
    """

    print(subprocess.Popen(['ls', '-lah', '/usr/bin/env']).communicate())
    print(subprocess.Popen(['which', 'env']).communicate())
    print(subprocess.Popen(['which', 'bash']).communicate())
    print(subprocess.Popen(['echo $PATH'], shell=True).communicate())

    run_command = f'{get_job_run_file_path(job)}'
    run_output = subprocess.Popen([run_command], '&')

    job_execution = delayed_job_models.JobExecution(
        hostname=socket.gethostname(),
        command=run_command,
        pid=run_output.pid,
        run_dir=get_job_run_dir(job)
    )

    delayed_job_models.add_job_execution_to_job(job, job_execution)
