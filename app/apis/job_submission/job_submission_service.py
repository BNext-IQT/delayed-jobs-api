"""
This module submits jobs to the EBI queue
"""
from app.apis.models import delayed_job_models
from app.config import RUN_CONFIG
from pathlib import Path
import os
import stat
from app.authorisation import token_generator
import shutil
import subprocess
import socket


JOBS_RUN_DIR = RUN_CONFIG.get('jobs_run_dir')
if JOBS_RUN_DIR is None:
    JOBS_RUN_DIR = str(Path().absolute()) + '/jobs_run'
    os.makedirs(JOBS_RUN_DIR, exist_ok=True)

print('------------------------------------------------------------------------------')
print('JOBS_RUN_DIR: ', JOBS_RUN_DIR)
print('------------------------------------------------------------------------------')

JOBS_SCRIPTS_DIR = str(Path().absolute()) + '/jobs_scripts'

RUN_PARAMS_FILENAME = 'run_params.yml'
RUN_FILE_NAME = 'run.sh'

SCRIPT_FILENAMES = {
    f'{delayed_job_models.JobTypes.TEST}': 'test_job.py',
    f'{delayed_job_models.JobTypes.SIMILARITY}': 'structure_search.py'
}

SCRIPT_FILES = {
    f'{delayed_job_models.JobTypes.TEST}':
        os.path.join(JOBS_SCRIPTS_DIR, SCRIPT_FILENAMES.get(str(delayed_job_models.JobTypes.TEST))),
    f'{delayed_job_models.JobTypes.SIMILARITY}':
        os.path.join(JOBS_SCRIPTS_DIR, SCRIPT_FILENAMES.get(str(delayed_job_models.JobTypes.SIMILARITY))),
}


def submit_job(job_type, job_params):
    """Submit job to the queue"""
    job = delayed_job_models.get_or_create(job_type, job_params)
    prepare_run_folder(job)
    must_run_jobs = RUN_CONFIG.get('run_jobs', True)
    if must_run_jobs:
        run_job(job)

    return job.public_dict()


def get_job_run_dir(job):
    return os.path.join(JOBS_RUN_DIR, job.id)


def get_job_run_file_path(job):
    return os.path.join(get_job_run_dir(job), RUN_FILE_NAME)


def prepare_run_folder(job):

    job_run_dir = get_job_run_dir(job)
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
        JOB_PARAMS=f'{job.raw_params}'
    )

    run_params_path = os.path.join(job_run_dir, RUN_PARAMS_FILENAME)

    # delete file if existed before, just in case
    if os.path.exists(run_params_path):
        os.remove(run_params_path)

    with open(run_params_path, 'w') as out_file:
        out_file.write(run_params)

    job_script = SCRIPT_FILES.get(str(job.type))
    script_path = os.path.join(job_run_dir, SCRIPT_FILENAMES.get(str(job.type)))
    shutil.copyfile(job_script, script_path)

    # make sure file is executable
    st = os.stat(script_path)
    os.chmod(script_path, st.st_mode | stat.S_IEXEC)

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
    st = os.stat(run_file_path)
    os.chmod(run_file_path, st.st_mode | stat.S_IEXEC)


def run_job(job):

    print('GOING TO RUN: ', job.id)
    run_command = f'{get_job_run_file_path(job)}'
    print('run_command: ', run_command)

    run_output = subprocess.Popen([run_command, '&'])

    job_execution = delayed_job_models.JobExecution(
        hostname=socket.gethostname(),
        command=run_command,
        pid=run_output.pid,
        run_dir=get_job_run_dir(job)
    )

    delayed_job_models.add_job_execution_to_job(job, job_execution)

    print('pid: ', run_output.pid)

